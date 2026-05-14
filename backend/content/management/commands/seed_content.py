from django.apps import apps
from django.core.management.base import BaseCommand, CommandError

from ...models import CompanionContent, SystemConfig


BASE_CONFIGS = {
    "push_frequency": {
        "value": {"times_per_day": 2},
        "description": "Default reminder pushes per day.",
        "is_public": True,
    },
    "reminder_window": {
        "value": {"start": "09:00", "end": "21:00"},
        "description": "Local time window for reminders.",
        "is_public": True,
    },
    "negative_emergency_days": {
        "value": {"days": 3},
        "description": "Consecutive negative-emotion days before emergency attention is suggested.",
        "is_public": False,
    },
}


def _emotion_label(tag):
    for attr in ("name", "label", "code", "slug"):
        if hasattr(tag, attr):
            value = getattr(tag, attr)
            if value:
                return str(value)
    return str(tag.pk)


class Command(BaseCommand):
    help = "Seed companion content and base system configs."

    def handle(self, *args, **options):
        try:
            emotion_tag_model = apps.get_model("emotions", "EmotionTag")
        except LookupError as exc:
            raise CommandError("emotions.EmotionTag is required before seeding content.") from exc

        config_count = 0
        for key, defaults in BASE_CONFIGS.items():
            _, created = SystemConfig.objects.update_or_create(key=key, defaults=defaults)
            config_count += int(created)

        content_count = 0
        tags = list(emotion_tag_model.objects.all())
        if not tags:
            self.stdout.write(self.style.WARNING("No emotion tags found; only system configs were seeded."))

        for tag in tags:
            label = _emotion_label(tag)
            items = (
                {
                    "content_type": CompanionContent.CONTENT_TYPE_PHRASE,
                    "title": f"{label} grounding phrase",
                    "body": "Take one slow breath. This feeling can be noticed without being obeyed.",
                    "weight": 10,
                },
                {
                    "content_type": CompanionContent.CONTENT_TYPE_ADVICE,
                    "title": f"{label} small next step",
                    "body": "Write down one thing you need in the next ten minutes, then choose the smallest possible action.",
                    "weight": 8,
                },
            )
            for item in items:
                _, created = CompanionContent.objects.update_or_create(
                    emotion_tag=tag,
                    content_type=item["content_type"],
                    title=item["title"],
                    defaults={
                        "body": item["body"],
                        "resource_url": "",
                        "weight": item["weight"],
                        "is_active": True,
                    },
                )
                content_count += int(created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed complete: {content_count} new companion contents, {config_count} new system configs."
            )
        )
