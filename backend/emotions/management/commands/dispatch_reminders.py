from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_datetime

from emotions.reminders import run_reminder_scheduler


class Command(BaseCommand):
    help = "Scan due reminder preferences, dispatch reminder pushes, and retry failed reminder logs."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100, help="Maximum number of due users to dispatch per run.")
        parser.add_argument("--retry-limit", type=int, default=20, help="Maximum number of retry logs to process per run.")
        parser.add_argument("--dry-run", action="store_true", help="Only print due users without sending reminders.")
        parser.add_argument(
            "--now",
            type=str,
            default="",
            help="Override current time with an ISO-8601 datetime for testing or backfill runs.",
        )

    def handle(self, *args, **options):
        now = None
        if options["now"]:
            now = parse_datetime(options["now"])
            if now is None:
                raise CommandError("--now must be a valid ISO-8601 datetime.")

        result = run_reminder_scheduler(
            now=now,
            dispatch_limit=options["limit"],
            retry_limit=options["retry_limit"],
            dry_run=options["dry_run"],
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Reminder scheduler finished: "
                f"due={result['scanned_due_users']} "
                f"triggered={result['triggered_users']} "
                f"dispatch_logs={result['dispatch_logs']} "
                f"retried={result['retried_logs']} "
                f"dry_run={str(result['dry_run']).lower()}"
            )
        )
        if result["user_ids"]:
            self.stdout.write(f"user_ids={','.join(str(user_id) for user_id in result['user_ids'])}")
