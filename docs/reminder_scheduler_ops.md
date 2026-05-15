# Reminder Scheduler Ops

## Purpose

`dispatch_reminders` is the minimum production-ready scheduler entrypoint for emotion reminders. It does not require Celery and is intended to be invoked by cron, systemd timer, or any external scheduler.

## Command

```bash
cd backend
python manage.py dispatch_reminders --limit=100 --retry-limit=20
```

Optional flags:

- `--dry-run`: print the due user ids without sending reminders
- `--now=2026-05-15T10:00:00+08:00`: override current time for backfill or smoke tests
- `--limit`: cap how many due users are dispatched in one run
- `--retry-limit`: cap how many retryable reminder logs are retried in one run

## Suggested schedule

Run the command every 5 minutes:

```cron
*/5 * * * * cd /path/to/MoodFlow/backend && /path/to/python manage.py dispatch_reminders --limit=100 --retry-limit=20 >> /var/log/moodflow-reminders.log 2>&1
```

## Current behavior

- Scans enabled users with at least one active device token
- Respects `timezone`, `reminder_time`, `quiet_hours_start`, `quiet_hours_end`, and `frequency_per_day`
- Uses `last_triggered_at` to avoid duplicate dispatch within the configured frequency interval
- Reuses the existing retry queue by processing `ReminderDispatchLog(status=retrying, next_retry_at<=now)`

## Current limits

- This is a polling scheduler, not a queue worker
- `frequency_per_day` is enforced as a minimum interval between sends, not as exact evenly spaced wall-clock slots
- Real Firebase delivery is still blocked on provider integration and credentials; production rollout still needs the real provider wired in
