from __future__ import annotations

from django.core.management.base import BaseCommand

from emotions.models import EmotionRecord
from emotions.security import is_encrypted_payload, prepare_text_for_storage


class Command(BaseCommand):
    help = "Encrypt legacy emotion records where is_encrypted is true but the stored payload is still plaintext."

    def handle(self, *args, **options):
        updated = 0
        queryset = EmotionRecord.objects.filter(is_encrypted=True).exclude(emotion_text="")
        for record in queryset.iterator():
            if is_encrypted_payload(record.emotion_text):
                continue
            record.emotion_text = prepare_text_for_storage(record.emotion_text, encrypt=True)
            record.save(update_fields=["emotion_text", "updated_at"])
            updated += 1
        self.stdout.write(self.style.SUCCESS(f"Encrypted {updated} legacy emotion records."))
