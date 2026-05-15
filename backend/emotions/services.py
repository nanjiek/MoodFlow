from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from typing import Iterable

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone

from mlops.services import call_model_service

from .models import EmotionAnalysis, EmotionRecord
from .presentation import build_weekly_summary, emotion_presentation
from .security import decrypt_text


NEGATIVE_LABELS = {"anxious", "sad", "irritable", "tired"}


def sync_record_analysis(record: EmotionRecord) -> EmotionAnalysis:
    plain_text = decrypt_text(record.emotion_text or "", is_encrypted=record.is_encrypted)
    result = call_model_service(plain_text, selected_label=record.tag.code)
    predicted_label = str(result.get("label") or record.tag.code)
    confidence = _bounded_float(result.get("confidence"), 0)
    stored_intensity = min(10, max(0, round(_bounded_float(result.get("intensity"), confidence) * 10)))
    keywords = list(result.get("keywords") or [])
    cause = str(result.get("explanation") or result.get("cause") or "")

    analysis, _ = EmotionAnalysis.objects.update_or_create(
        record=record,
        defaults={
            "predicted_label": predicted_label,
            "confidence": confidence,
            "keywords": keywords,
            "intensity": stored_intensity,
            "trend": _infer_trend(record.user_id, predicted_label, record.recorded_at),
            "cause": cause,
            "model_version": str(result.get("model_version") or ""),
            "raw_result": result,
        },
    )
    return analysis


def build_daily_report(user_id: int, target_day) -> dict[str, object]:
    start_at, end_at = _day_bounds(target_day)
    records = list(
        EmotionRecord.objects.select_related("tag", "analysis")
        .filter(user_id=user_id, recorded_at__gte=start_at, recorded_at__lte=end_at)
        .order_by("recorded_at", "id")
    )
    if not records:
        return {
            "date": target_day.isoformat(),
            "record_count": 0,
            "dominant_emotion": None,
            "keywords": [],
            "summary": "这一天还没有情绪记录，先记下一点点感受也很好。",
        }

    labels, keywords = _labels_and_keywords(records)
    dominant_label, dominant_count = Counter(labels).most_common(1)[0]
    dominant = emotion_presentation(dominant_label)
    return {
        "date": target_day.isoformat(),
        "record_count": len(records),
        "dominant_emotion": dominant,
        "keywords": keywords[:5],
        "summary": f"这一天你最常处在“{dominant['display_name']}”的状态，共记录了 {dominant_count} 次。",
    }


def build_user_weekly_report(user_id: int, end_day=None, days: int = 7) -> dict[str, object]:
    if end_day is None:
        end_day = timezone.localdate()
    start_day = end_day - timedelta(days=days - 1)
    start_at, _ = _day_bounds(start_day)
    _, end_at = _day_bounds(end_day)
    records = list(
        EmotionRecord.objects.select_related("tag", "analysis")
        .filter(user_id=user_id, recorded_at__gte=start_at, recorded_at__lte=end_at)
        .order_by("recorded_at", "id")
    )

    summary_records = []
    labels, keywords = _labels_and_keywords(records)
    for label, keyword_list in zip(labels, keywords_per_record(records)):
        summary_records.append({"label": label, "keywords": keyword_list})

    weekly = build_weekly_summary(summary_records)
    label_counts = Counter(labels)
    total = sum(label_counts.values()) or 1
    weekly.update(
        {
            "start_date": start_day.isoformat(),
            "end_date": end_day.isoformat(),
            "record_count": len(records),
            "negative_days": sum(label in NEGATIVE_LABELS for label in labels),
            "emotion_breakdown": [
                {
                    "code": label,
                    "count": count,
                    "ratio": round(count / total, 4),
                    "detail": emotion_presentation(label),
                }
                for label, count in label_counts.most_common()
            ],
            "top_keywords": keywords[:8],
        }
    )
    return weekly


def build_growth_curve(user_id: int, days: int = 7) -> dict[str, object]:
    end_day = timezone.localdate()
    start_day = end_day - timedelta(days=days - 1)
    start_at, _ = _day_bounds(start_day)
    _, end_at = _day_bounds(end_day)

    queryset = (
        EmotionRecord.objects.select_related("analysis", "tag")
        .filter(user_id=user_id, recorded_at__gte=start_at, recorded_at__lte=end_at)
        .order_by("recorded_at", "id")
    )

    day_groups: dict[str, list[EmotionRecord]] = {}
    for record in queryset:
        key = timezone.localtime(record.recorded_at).date().isoformat()
        day_groups.setdefault(key, []).append(record)

    series = []
    current = start_day
    while current <= end_day:
        key = current.isoformat()
        records = day_groups.get(key, [])
        labels, _ = _labels_and_keywords(records)
        counter = Counter(labels)
        dominant_label = counter.most_common(1)[0][0] if counter else None
        total = sum(counter.values()) or 1
        series.append(
            {
                "date": key,
                "dominant_emotion": emotion_presentation(dominant_label) if dominant_label else None,
                "emotion_breakdown": [
                    {
                        "code": label,
                        "count": count,
                        "ratio": round(count / total, 4),
                    }
                    for label, count in counter.most_common()
                ],
                "record_count": len(records),
            }
        )
        current += timedelta(days=1)

    return {
        "start_date": start_day.isoformat(),
        "end_date": end_day.isoformat(),
        "days": days,
        "series": series,
    }


def keywords_per_record(records: Iterable[EmotionRecord]) -> list[list[str]]:
    values = []
    for record in records:
        analysis = getattr(record, "analysis", None)
        values.append(list(getattr(analysis, "keywords", []) or []))
    return values


def _labels_and_keywords(records: Iterable[EmotionRecord]) -> tuple[list[str], list[str]]:
    labels: list[str] = []
    keywords: list[str] = []
    for record in records:
        analysis = getattr(record, "analysis", None)
        label = getattr(analysis, "predicted_label", None) or record.tag.code
        labels.append(label)
        keywords.extend(list(getattr(analysis, "keywords", []) or []))
    top_keywords = [keyword for keyword, _ in Counter(keywords).most_common()]
    return labels, top_keywords


def _infer_trend(user_id: int, label: str, recorded_at) -> str:
    since = recorded_at - timedelta(days=7)
    recent_labels = list(
        EmotionAnalysis.objects.filter(record__user_id=user_id, record__recorded_at__gte=since)
        .values_list("predicted_label", flat=True)[:6]
    )
    negative_before = sum(item in NEGATIVE_LABELS for item in recent_labels)
    negative_after = negative_before + int(label in NEGATIVE_LABELS)
    if negative_after >= negative_before + 2:
        return EmotionAnalysis.TREND_RISING
    if negative_after < negative_before:
        return EmotionAnalysis.TREND_FALLING
    return EmotionAnalysis.TREND_STABLE


def _day_bounds(day):
    start_at = timezone.make_aware(datetime.combine(day, datetime.min.time()), timezone.get_current_timezone())
    end_at = timezone.make_aware(datetime.combine(day, datetime.max.time()), timezone.get_current_timezone())
    return start_at, end_at


def _bounded_float(value, default):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = default
    return min(1.0, max(0.0, parsed))
