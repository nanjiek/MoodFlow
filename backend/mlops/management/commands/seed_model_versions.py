from __future__ import annotations

import json
import re
from datetime import datetime, timezone as dt_timezone
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from mlops.models import ModelVersion


class Command(BaseCommand):
    help = "Seed model version metadata from model_service/artifacts/baseline-clean-v4/metadata.json."

    def add_arguments(self, parser):
        parser.add_argument(
            "--metadata",
            default="model_service/artifacts/baseline-clean-v4/metadata.json",
            help="Path to metadata.json under a model artifact directory.",
        )
        parser.add_argument("--name", default="", help="Model name override.")
        parser.add_argument("--model-type", default="", help="Model type override, e.g. baseline or transformer.")
        parser.add_argument("--activate", action="store_true", help="Activate this version after seeding.")

    @transaction.atomic
    def handle(self, *args, **options):
        metadata_path = _resolve_path(options["metadata"])
        if not metadata_path.exists():
            raise CommandError(f"Model metadata does not exist: {metadata_path}")

        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid model metadata JSON: {metadata_path}") from exc

        version = str(metadata.get("version") or metadata.get("model_version") or metadata_path.parent.name).strip()
        if not version:
            raise CommandError("Model metadata must include version or model_version.")

        existing_active = ModelVersion.objects.filter(is_active=True).exists()
        should_activate = options["activate"] or not existing_active

        model_version, created = ModelVersion.objects.update_or_create(
            version=version,
            defaults={
                "name": options["name"] or metadata.get("name") or "MoodFlow baseline",
                "model_type": options["model_type"] or metadata.get("model_type") or "baseline",
                "artifact_path": str(metadata_path.parent),
                "metrics": metadata,
                "trained_at": _parse_trained_at(metadata, version),
            },
        )

        if should_activate:
            ModelVersion.objects.exclude(pk=model_version.pk).update(is_active=False)
            model_version.is_active = True
            model_version.save(update_fields=("is_active", "updated_at"))

        action = "created" if created else "updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"Model version {version!r} {action}; active={model_version.is_active}; artifact={metadata_path.parent}."
            )
        )


def _resolve_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path

    for base in (Path.cwd(), settings.BASE_DIR, settings.BASE_DIR.parent):
        candidate = base / path
        if candidate.exists():
            return candidate
    return settings.BASE_DIR.parent / path


def _parse_trained_at(metadata: dict[str, object], version: str):
    for key in ("trained_at", "created_at", "timestamp"):
        raw_value = metadata.get(key)
        if not raw_value:
            continue

        if isinstance(raw_value, (int, float)):
            return datetime.fromtimestamp(float(raw_value), tz=dt_timezone.utc)

        parsed = parse_datetime(str(raw_value))
        if parsed:
            if timezone.is_naive(parsed):
                return timezone.make_aware(parsed, timezone=dt_timezone.utc)
            return parsed

    match = re.search(r"(\d{14})", version)
    if match:
        parsed = datetime.strptime(match.group(1), "%Y%m%d%H%M%S")
        return timezone.make_aware(parsed, timezone=dt_timezone.utc)

    return timezone.now()
