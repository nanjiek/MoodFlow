from datetime import timedelta

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from analytics.models import FeatureUsageLog


FEATURE_ACTIONS = (
    ("emotion_record", "create"),
    ("emotion_record", "view"),
    ("emotion_analysis", "view"),
    ("tree_hole", "post"),
    ("tree_hole", "comment"),
    ("companion_content", "view"),
    ("companion_content", "favorite"),
    ("breathing_exercise", "start"),
    ("breathing_exercise", "complete"),
    ("daily_report", "view"),
)


class Command(BaseCommand):
    help = "Seed demo feature usage logs for analytics statistics."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=14, help="Number of recent days to cover.")
        parser.add_argument("--users", type=int, default=8, help="Number of demo users to spread events across.")
        parser.add_argument("--events", type=int, default=120, help="Number of usage events to create.")

    def handle(self, *args, **options):
        days = max(options["days"], 1)
        users = max(options["users"], 1)
        events = max(options["events"], 1)
        user_ids = _demo_user_ids(users)
        now = timezone.now()

        with transaction.atomic():
            for index in range(events):
                feature, action = FEATURE_ACTIONS[index % len(FEATURE_ACTIONS)]
                day_offset = index % days
                created_at = now - timedelta(days=day_offset, minutes=index * 11)
                log = FeatureUsageLog.objects.create(
                    feature=feature,
                    user_id=str(user_ids[index % len(user_ids)]),
                    action=action,
                    metadata={
                        "seed": True,
                        "seed_command": "seed_usage_logs",
                        "demo_index": index,
                    },
                )
                FeatureUsageLog.objects.filter(pk=log.pk).update(created_at=created_at)

        self.stdout.write(self.style.SUCCESS(f"Seeded {events} demo feature usage logs."))


def _demo_user_ids(limit):
    user_ids = []
    try:
        app_user_model = apps.get_model("emotions", "AppUser")
    except (LookupError, RuntimeError):
        app_user_model = None

    if app_user_model is not None:
        user_ids = [str(pk) for pk in app_user_model.objects.order_by("id").values_list("id", flat=True)[:limit]]

    next_id = 900001
    while len(user_ids) < limit:
        user_ids.append(str(next_id))
        next_id += 1
    return user_ids
