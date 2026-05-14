from __future__ import annotations

import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from mlops.models import TrainingSample


class Command(BaseCommand):
    help = "Import processed emotion training samples into mlops_training_sample."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default="data/processed/moodflow_emotions.csv",
            help="CSV path. Defaults to data/processed/moodflow_emotions.csv under the repository root.",
        )
        parser.add_argument("--source", default="", help="Override source for every imported row.")
        parser.add_argument("--limit", type=int, default=0, help="Maximum rows to import; 0 means all rows.")
        parser.add_argument("--batch-size", type=int, default=2000, help="Rows per bulk insert batch.")

    def handle(self, *args, **options):
        csv_path = _resolve_path(options["path"])
        if not csv_path.exists():
            raise CommandError(f"Training sample CSV does not exist: {csv_path}")

        created_count = 0
        skipped_count = 0
        limit = options["limit"]
        batch_size = max(options["batch_size"], 1)
        existing_keys = set(TrainingSample.objects.values_list("text", "source", "raw_label"))
        pending: list[TrainingSample] = []

        with csv_path.open(encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            for index, row in enumerate(reader, start=1):
                if limit and index > limit:
                    break

                text = _first_value(row, "text", "content", "utterance", "Utterance")
                raw_label = _first_value(row, "raw_label", "emotion", "Emotion", "label")
                mapped_label = _first_value(row, "mapped_label", "mapped", "label") or raw_label
                source = options["source"] or _first_value(row, "source") or "processed_import"

                if not text or not mapped_label:
                    skipped_count += 1
                    continue

                key = (text, source, raw_label)
                if key in existing_keys:
                    skipped_count += 1
                    continue
                existing_keys.add(key)

                pending.append(
                    TrainingSample(
                        text=text,
                        raw_label=raw_label,
                        mapped_label=mapped_label,
                        source=source,
                        status=TrainingSample.Status.ACTIVE,
                    )
                )
                if len(pending) >= batch_size:
                    created_count += _flush_batch(pending)

        created_count += _flush_batch(pending)

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported training samples from {csv_path}: created={created_count}, "
                f"skipped={skipped_count}."
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


def _first_value(row: dict[str, str], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None:
            return str(value).strip()
    return ""


def _flush_batch(pending: list[TrainingSample]) -> int:
    if not pending:
        return 0
    count = len(pending)
    TrainingSample.objects.bulk_create(pending, batch_size=count)
    pending.clear()
    return count
