from __future__ import annotations

import csv
import io
import json

from django.utils import timezone

from .models import EmotionAnalysis, EmotionDataExportTask, EmotionRecord
from .security import decrypt_text


def create_export_task(*, user, file_format: str, start_at, end_at) -> EmotionDataExportTask:
    task = EmotionDataExportTask.objects.create(
        user=user,
        file_format=file_format,
        status=EmotionDataExportTask.Status.PROCESSING,
        start_at=start_at,
        end_at=end_at,
    )
    try:
        payload_rows = export_user_emotion_data(user=user, start_at=start_at, end_at=end_at)
        content = render_export_content(payload_rows, file_format=file_format)
        task.status = EmotionDataExportTask.Status.COMPLETED
        task.record_count = len(payload_rows)
        task.file_name = f"moodflow-export-{user.id}-{timezone.now():%Y%m%d%H%M%S}.{file_format}"
        task.content = content
        task.metadata = {"record_ids": [row["record_id"] for row in payload_rows]}
        task.completed_at = timezone.now()
        task.save(
            update_fields=[
                "status",
                "record_count",
                "file_name",
                "content",
                "metadata",
                "completed_at",
                "updated_at",
            ]
        )
    except Exception as exc:
        task.status = EmotionDataExportTask.Status.FAILED
        task.error_message = str(exc)
        task.save(update_fields=["status", "error_message", "updated_at"])
        raise
    return task


def export_user_emotion_data(*, user, start_at, end_at) -> list[dict]:
    queryset = (
        EmotionRecord.objects.select_related("tag")
        .filter(user=user, recorded_at__gte=start_at, recorded_at__lte=end_at)
        .order_by("recorded_at", "id")
    )
    analyses = {
        analysis.record_id: analysis
        for analysis in EmotionAnalysis.objects.filter(record__in=queryset).select_related("record")
    }
    rows = []
    for record in queryset:
        analysis = analyses.get(record.id)
        rows.append(
            {
                "record_id": record.id,
                "recorded_at": record.recorded_at.isoformat(),
                "selected_label": record.tag.code,
                "emotion_text": decrypt_text(record.emotion_text, is_encrypted=record.is_encrypted),
                "is_encrypted": record.is_encrypted,
                "is_collect": record.is_collect,
                "source": record.source,
                "analysis": {
                    "predicted_label": analysis.predicted_label if analysis else "",
                    "confidence": analysis.confidence if analysis else 0,
                    "keywords": analysis.keywords if analysis else [],
                    "intensity": analysis.intensity if analysis else 0,
                    "trend": analysis.trend if analysis else "",
                    "cause": analysis.cause if analysis else "",
                    "model_version": analysis.model_version if analysis else "",
                },
            }
        )
    return rows


def render_export_content(rows: list[dict], *, file_format: str) -> str:
    if file_format == EmotionDataExportTask.Format.JSON:
        return json.dumps(rows, ensure_ascii=False, indent=2)
    if file_format == EmotionDataExportTask.Format.CSV:
        buffer = io.StringIO()
        writer = csv.DictWriter(
            buffer,
            fieldnames=[
                "record_id",
                "recorded_at",
                "selected_label",
                "emotion_text",
                "is_encrypted",
                "is_collect",
                "source",
                "predicted_label",
                "confidence",
                "keywords",
                "intensity",
                "trend",
                "cause",
                "model_version",
            ],
        )
        writer.writeheader()
        for row in rows:
            analysis = row["analysis"]
            writer.writerow(
                {
                    "record_id": row["record_id"],
                    "recorded_at": row["recorded_at"],
                    "selected_label": row["selected_label"],
                    "emotion_text": row["emotion_text"],
                    "is_encrypted": row["is_encrypted"],
                    "is_collect": row["is_collect"],
                    "source": row["source"],
                    "predicted_label": analysis["predicted_label"],
                    "confidence": analysis["confidence"],
                    "keywords": "|".join(analysis["keywords"]),
                    "intensity": analysis["intensity"],
                    "trend": analysis["trend"],
                    "cause": analysis["cause"],
                    "model_version": analysis["model_version"],
                }
            )
        return buffer.getvalue()
    raise ValueError("Unsupported export format.")
