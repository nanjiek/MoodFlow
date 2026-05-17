from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from urllib import error as urlerror
from urllib import request as urlrequest
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from analytics.services import log_feature_usage
from content.services import recommend_contents

from .models import AppUser, EmotionAnalysis, EmotionRecord, ReminderDispatchLog, UserDeviceToken, UserReminderPreference


logger = logging.getLogger(__name__)


def _firebase_mock_enabled() -> bool:
    return bool(getattr(settings, "FIREBASE_MOCK_MODE", getattr(settings, "DEBUG", False)))


def _reminder_retry_delay_seconds() -> int:
    return int(getattr(settings, "REMINDER_RETRY_DELAY_SECONDS", 300))


def _expo_push_timeout_seconds() -> int:
    return int(getattr(settings, "EXPO_PUSH_TIMEOUT_SECONDS", 10))


def _expo_push_api_url() -> str:
    return str(getattr(settings, "EXPO_PUSH_API_URL", "https://exp.host/--/api/v2/push/send"))


def _is_expo_push_token(token: str) -> bool:
    return token.startswith("ExponentPushToken[") or token.startswith("ExpoPushToken[")


class FirebasePushService:
    def send_message(self, *, token: str, title: str, body: str, data: dict | None = None) -> dict:
        raise NotImplementedError


class MockFirebasePushService(FirebasePushService):
    def send_message(self, *, token: str, title: str, body: str, data: dict | None = None) -> dict:
        response = {
            "provider": "mock-firebase",
            "token": token,
            "title": title,
            "body": body,
            "data": data or {},
            "message_id": f"mock-{timezone.now().timestamp()}",
        }
        logger.info("Mock Firebase push sent: %s", response)
        return response


def _send_expo_push_request(message: dict) -> dict:
    payload = json.dumps(message).encode("utf-8")
    request = urlrequest.Request(
        _expo_push_api_url(),
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate",
        },
        method="POST",
    )
    try:
        with urlrequest.urlopen(request, timeout=_expo_push_timeout_seconds()) as response:
            raw_body = response.read().decode("utf-8")
    except urlerror.HTTPError as exc:
        raw_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Expo push request failed with HTTP {exc.code}: {raw_body}") from exc
    except urlerror.URLError as exc:
        raise RuntimeError(f"Expo push request failed: {exc.reason}") from exc

    try:
        parsed = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Expo push returned invalid JSON: {raw_body}") from exc
    return parsed


class ExpoPushService(FirebasePushService):
    def send_message(self, *, token: str, title: str, body: str, data: dict | None = None) -> dict:
        message = {
            "to": token,
            "title": title,
            "body": body,
            "data": data or {},
            "sound": "default",
        }
        parsed = _send_expo_push_request(message)
        result = parsed.get("data")
        if isinstance(result, dict) and result.get("status") == "error":
            raise RuntimeError(result.get("message", "Expo push returned an error ticket."))
        return {
            "provider": "expo",
            "ticket": result,
            "raw": parsed,
        }


def get_push_service(token: str = "") -> FirebasePushService:
    if token and _is_expo_push_token(token):
        return ExpoPushService()
    if _firebase_mock_enabled():
        return MockFirebasePushService()
    raise RuntimeError("Real Firebase push requires firebase_admin integration and credentials configuration.")


def get_or_create_reminder_preference(user: AppUser) -> UserReminderPreference:
    preference, _ = UserReminderPreference.objects.get_or_create(user=user)
    return preference


def resolve_preference_timezone(preference: UserReminderPreference) -> ZoneInfo:
    tz_name = preference.timezone or str(timezone.get_current_timezone())
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        logger.warning("Unknown reminder timezone %s for user %s, fallback to server timezone.", tz_name, preference.user_id)
        return timezone.get_current_timezone()


def is_in_quiet_hours(preference: UserReminderPreference, current_local_time) -> bool:
    start = preference.quiet_hours_start
    end = preference.quiet_hours_end
    if start == end:
        return False
    if start < end:
        return start <= current_local_time < end
    return current_local_time >= start or current_local_time < end


def reminder_interval(preference: UserReminderPreference) -> timedelta:
    frequency = max(int(preference.frequency_per_day or 1), 1)
    return timedelta(seconds=86400 / frequency)


def is_preference_due(preference: UserReminderPreference, *, now: datetime | None = None) -> bool:
    if not preference.enabled or not preference.user.is_active:
        return False
    if not preference.user.device_tokens.filter(is_active=True).exists():
        return False

    current = now or timezone.now()
    tzinfo = resolve_preference_timezone(preference)
    local_now = timezone.localtime(current, tzinfo)

    if is_in_quiet_hours(preference, local_now.timetz().replace(tzinfo=None)):
        return False

    if preference.last_triggered_at:
        local_last = timezone.localtime(preference.last_triggered_at, tzinfo)
        if local_now - local_last < reminder_interval(preference):
            return False

    if local_now.timetz().replace(tzinfo=None) < preference.reminder_time:
        return False
    return True


def find_due_reminder_preferences(*, now: datetime | None = None, limit: int = 100) -> list[UserReminderPreference]:
    queryset = (
        UserReminderPreference.objects.select_related("user")
        .filter(enabled=True, user__is_active=True, user__device_tokens__is_active=True)
        .distinct()
        .order_by("last_triggered_at", "id")
    )

    due_preferences: list[UserReminderPreference] = []
    for preference in queryset.iterator():
        if is_preference_due(preference, now=now):
            due_preferences.append(preference)
            if len(due_preferences) >= limit:
                break
    return due_preferences


def register_device_token(*, user: AppUser, token: str, platform: str, device_id: str = "") -> UserDeviceToken:
    device, _ = UserDeviceToken.objects.update_or_create(
        token=token,
        defaults={
            "user": user,
            "platform": platform,
            "device_id": device_id,
            "is_active": True,
            "last_seen_at": timezone.now(),
        },
    )
    return device


def trigger_user_reminder(user: AppUser) -> list[ReminderDispatchLog]:
    preference = get_or_create_reminder_preference(user)
    if not preference.enabled:
        return []

    devices = list(user.device_tokens.filter(is_active=True).order_by("id"))
    if not devices:
        return []

    title, body, extra = build_reminder_message(user)
    logs: list[ReminderDispatchLog] = []
    for device in devices:
        push_service = get_push_service(device.token)
        log = ReminderDispatchLog.objects.create(
            user=user,
            device=device,
            status=ReminderDispatchLog.Status.PENDING,
            payload={"title": title, "body": body, "data": extra},
        )
        try:
            response = push_service.send_message(token=device.token, title=title, body=body, data=extra)
        except Exception as exc:
            log.status = ReminderDispatchLog.Status.RETRYING
            log.attempt_count = 1
            log.last_error = str(exc)
            log.next_retry_at = timezone.now() + timedelta(seconds=_reminder_retry_delay_seconds())
            log.save(update_fields=["status", "attempt_count", "last_error", "next_retry_at", "updated_at"])
        else:
            log.status = ReminderDispatchLog.Status.SENT
            log.attempt_count = 1
            log.sent_at = timezone.now()
            log.response_payload = response
            log.save(update_fields=["status", "attempt_count", "sent_at", "response_payload", "updated_at"])
        logs.append(log)

    preference.last_triggered_at = timezone.now()
    preference.save(update_fields=["last_triggered_at", "updated_at"])
    log_feature_usage("emotion_reminder", action="trigger", user_id=str(user.pk), metadata={"dispatch_count": len(logs)})
    return logs


def dispatch_due_reminders(*, now: datetime | None = None, limit: int = 100, dry_run: bool = False) -> dict:
    current = now or timezone.now()
    due_preferences = find_due_reminder_preferences(now=current, limit=limit)
    result = {
        "scanned_due_users": len(due_preferences),
        "triggered_users": 0,
        "dispatch_logs": 0,
        "dry_run": dry_run,
        "user_ids": [],
    }
    if dry_run:
        result["user_ids"] = [preference.user_id for preference in due_preferences]
        return result

    for preference in due_preferences:
        with transaction.atomic():
            locked = (
                UserReminderPreference.objects.select_for_update()
                .select_related("user")
                .get(pk=preference.pk)
            )
            if not is_preference_due(locked, now=current):
                continue
            logs = trigger_user_reminder(locked.user)
        if logs:
            result["triggered_users"] += 1
            result["dispatch_logs"] += len(logs)
            result["user_ids"].append(locked.user_id)
    return result


def retry_failed_dispatches(limit: int = 20) -> int:
    now = timezone.now()
    queryset = ReminderDispatchLog.objects.select_related("device", "user").filter(
        status=ReminderDispatchLog.Status.RETRYING,
        next_retry_at__lte=now,
    )[:limit]
    processed = 0
    for log in queryset:
        if log.device is None or not log.device.is_active:
            log.status = ReminderDispatchLog.Status.FAILED
            log.last_error = "Device token is missing or inactive."
            log.save(update_fields=["status", "last_error", "updated_at"])
            processed += 1
            continue
        try:
            push_service = get_push_service(log.device.token)
            response = push_service.send_message(
                token=log.device.token,
                title=log.payload.get("title", ""),
                body=log.payload.get("body", ""),
                data=log.payload.get("data", {}),
            )
        except Exception as exc:
            log.attempt_count += 1
            log.last_error = str(exc)
            if log.attempt_count >= 3:
                log.status = ReminderDispatchLog.Status.FAILED
                log.next_retry_at = None
            else:
                log.next_retry_at = timezone.now() + timedelta(seconds=_reminder_retry_delay_seconds() * log.attempt_count)
            log.save(update_fields=["attempt_count", "last_error", "status", "next_retry_at", "updated_at"])
        else:
            log.status = ReminderDispatchLog.Status.SENT
            log.attempt_count += 1
            log.sent_at = timezone.now()
            log.next_retry_at = None
            log.response_payload = response
            log.save(update_fields=["status", "attempt_count", "sent_at", "next_retry_at", "response_payload", "updated_at"])
        processed += 1
    return processed


def run_reminder_scheduler(*, now: datetime | None = None, dispatch_limit: int = 100, retry_limit: int = 20, dry_run: bool = False) -> dict:
    current = now or timezone.now()
    dispatch_result = dispatch_due_reminders(now=current, limit=dispatch_limit, dry_run=dry_run)
    retry_count = 0 if dry_run else retry_failed_dispatches(limit=retry_limit)
    return {
        **dispatch_result,
        "retried_logs": retry_count,
        "executed_at": current.isoformat(),
        "dispatch_limit": dispatch_limit,
        "retry_limit": retry_limit,
    }


def build_reminder_message(user: AppUser) -> tuple[str, str, dict]:
    latest_record = (
        EmotionRecord.objects.select_related("tag")
        .filter(user=user)
        .order_by("-recorded_at", "-id")
        .first()
    )
    latest_analysis = None
    label = "plain"
    if latest_record is not None:
        latest_analysis = EmotionAnalysis.objects.filter(record=latest_record).order_by("-id").first()
        label = latest_analysis.predicted_label if latest_analysis and latest_analysis.predicted_label else latest_record.tag.code
    preferred_types = get_or_create_reminder_preference(user).preferred_content_types
    suggestions = recommend_contents(label, limit=1, preferred_types=preferred_types)
    suggestion = suggestions[0] if suggestions else None
    title = "MoodFlow 提醒"
    body = suggestion.body if suggestion and suggestion.body else "留一点时间给自己，记录一下此刻的心情。"
    extra = {
        "emotion_label": label,
        "content_type": suggestion.content_type if suggestion else "",
        "content_title": suggestion.title if suggestion else "",
    }
    return title, body, extra
