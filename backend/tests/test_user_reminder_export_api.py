from __future__ import annotations

import json
from datetime import datetime, timedelta
from io import StringIO

import pytest


pytest.importorskip("django")
pytest.importorskip("pytest_django")
pytest.importorskip("rest_framework")

from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from emotions.models import EmotionAnalysis, EmotionRecord, EmotionTag, ReminderDispatchLog
from emotions.reminders import dispatch_due_reminders
from emotions.security import prepare_text_for_storage


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def auth_headers(api_client: APIClient) -> dict[str, str]:
    response = api_client.post(
        "/api/auth/register/",
        {"phone": "13830303030", "password": "MoodFlowUser123!", "nickname": "Reminder User"},
        format="json",
    )
    token = response.json()["data"]["token"]
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def tags() -> dict[str, EmotionTag]:
    return {
        "happy": EmotionTag.objects.create(code="happy", name="Happy", sort_order=10, is_active=True),
        "sad": EmotionTag.objects.create(code="sad", name="Sad", sort_order=20, is_active=True),
    }


@pytest.mark.django_db
def test_device_registration_preference_and_reminder_trigger(
    api_client: APIClient,
    auth_headers: dict[str, str],
) -> None:
    register_device = api_client.post(
        "/api/emotions/devices/",
        {"token": "device-token-001", "platform": "android", "device_id": "pixel-1"},
        format="json",
        **auth_headers,
    )
    assert register_device.status_code == 200
    assert register_device.json()["data"]["platform"] == "android"

    preference_update = api_client.patch(
        "/api/emotions/reminder-preferences/",
        {"enabled": True, "frequency_per_day": 2, "preferred_content_types": ["phrase"]},
        format="json",
        **auth_headers,
    )
    assert preference_update.status_code == 200
    assert preference_update.json()["data"]["frequency_per_day"] == 2

    trigger_response = api_client.post(
        "/api/emotions/reminders/trigger/",
        format="json",
        **auth_headers,
    )
    assert trigger_response.status_code == 200
    trigger_payload = trigger_response.json()["data"]
    assert len(trigger_payload) == 1
    assert trigger_payload[0]["status"] == "sent"
    assert trigger_payload[0]["response_payload"]["provider"] == "mock-firebase"


@pytest.mark.django_db
def test_dispatch_due_reminders_scans_due_users(
    api_client: APIClient,
    auth_headers: dict[str, str],
) -> None:
    register_device = api_client.post(
        "/api/emotions/devices/",
        {"token": "device-token-002", "platform": "android", "device_id": "pixel-2"},
        format="json",
        **auth_headers,
    )
    assert register_device.status_code == 200

    preference_update = api_client.patch(
        "/api/emotions/reminder-preferences/",
        {
            "enabled": True,
            "timezone": "Asia/Shanghai",
            "reminder_time": "09:00:00",
            "quiet_hours_start": "23:00:00",
            "quiet_hours_end": "07:00:00",
            "frequency_per_day": 2,
        },
        format="json",
        **auth_headers,
    )
    assert preference_update.status_code == 200

    result = dispatch_due_reminders(now=datetime(2026, 5, 15, 10, 0, tzinfo=timezone.get_current_timezone()))
    assert result["scanned_due_users"] == 1
    assert result["triggered_users"] == 1
    assert result["dispatch_logs"] == 1

    second_run = dispatch_due_reminders(now=datetime(2026, 5, 15, 10, 30, tzinfo=timezone.get_current_timezone()))
    assert second_run["scanned_due_users"] == 0
    assert second_run["triggered_users"] == 0


@pytest.mark.django_db
def test_dispatch_due_reminders_respects_quiet_hours(
    api_client: APIClient,
    auth_headers: dict[str, str],
) -> None:
    register_device = api_client.post(
        "/api/emotions/devices/",
        {"token": "device-token-003", "platform": "android", "device_id": "pixel-3"},
        format="json",
        **auth_headers,
    )
    assert register_device.status_code == 200

    preference_update = api_client.patch(
        "/api/emotions/reminder-preferences/",
        {
            "enabled": True,
            "timezone": "Asia/Shanghai",
            "reminder_time": "06:30:00",
            "quiet_hours_start": "22:00:00",
            "quiet_hours_end": "08:00:00",
            "frequency_per_day": 1,
        },
        format="json",
        **auth_headers,
    )
    assert preference_update.status_code == 200

    result = dispatch_due_reminders(now=datetime(2026, 5, 15, 7, 0, tzinfo=timezone.get_current_timezone()))
    assert result["scanned_due_users"] == 0
    assert result["triggered_users"] == 0


@pytest.mark.django_db
def test_dispatch_reminders_command_runs_retry_flow(
    api_client: APIClient,
    auth_headers: dict[str, str],
) -> None:
    register_device = api_client.post(
        "/api/emotions/devices/",
        {"token": "device-token-004", "platform": "android", "device_id": "pixel-4"},
        format="json",
        **auth_headers,
    )
    assert register_device.status_code == 200
    device_id = register_device.json()["data"]["id"]

    owner_profile = api_client.get("/api/me/", **auth_headers)
    user_id = owner_profile.json()["data"]["id"]
    retry_log = ReminderDispatchLog.objects.create(
        user_id=user_id,
        device_id=device_id,
        status=ReminderDispatchLog.Status.RETRYING,
        payload={"title": "retry", "body": "retry body", "data": {"source": "test"}},
        attempt_count=1,
        next_retry_at=timezone.now() - timedelta(minutes=5),
    )

    out = StringIO()
    call_command(
        "dispatch_reminders",
        "--now=2026-05-15T10:00:00+08:00",
        "--limit=10",
        "--retry-limit=10",
        stdout=out,
    )

    retry_log.refresh_from_db()
    assert retry_log.status == ReminderDispatchLog.Status.SENT
    assert retry_log.attempt_count == 2
    assert "retried=1" in out.getvalue()


@pytest.mark.django_db
def test_export_json_csv_and_download_permission(
    api_client: APIClient,
    auth_headers: dict[str, str],
    tags: dict[str, EmotionTag],
) -> None:
    owner_profile = api_client.get("/api/me/", **auth_headers)
    owner_id = owner_profile.json()["data"]["id"]

    create_record = api_client.post(
        "/api/emotions/records/",
        {
            "selected_label": "happy",
            "text": "export me",
            "is_encrypted": True,
            "recorded_at": "2026-05-15T10:00:00+08:00",
        },
        format="json",
        **auth_headers,
    )
    assert create_record.status_code == 201
    record_id = create_record.json()["data"]["id"]
    record = EmotionRecord.objects.get(pk=record_id)
    EmotionAnalysis.objects.update_or_create(
        record=record,
        defaults={
            "predicted_label": "happy",
            "confidence": 0.95,
            "keywords": ["export", "happy"],
            "intensity": 7,
            "trend": EmotionAnalysis.TREND_STABLE,
            "cause": "export test",
            "model_version": "suite",
            "raw_result": {"label": "happy"},
        },
    )

    other_user = api_client.post(
        "/api/auth/register/",
        {"phone": "13830303031", "password": "MoodFlowUser123!", "nickname": "Other User"},
        format="json",
    )
    other_token = other_user.json()["data"]["token"]
    other_owner = api_client.get("/api/me/", HTTP_AUTHORIZATION=f"Bearer {other_token}")
    other_id = other_owner.json()["data"]["id"]
    EmotionRecord.objects.create(
        user_id=other_id,
        emotion_text=prepare_text_for_storage("other user's note", encrypt=False),
        tag=tags["sad"],
        recorded_at="2026-05-15T11:00:00+08:00",
    )

    export_json = api_client.post(
        "/api/emotions/exports/",
        {
            "file_format": "json",
            "start_at": "2026-05-15T00:00:00+08:00",
            "end_at": "2026-05-15T23:59:59+08:00",
        },
        format="json",
        **auth_headers,
    )
    assert export_json.status_code == 201
    export_payload = export_json.json()["data"]
    exported_rows = json.loads(export_payload["content"])
    assert len(exported_rows) == 1
    assert exported_rows[0]["record_id"] == record_id
    assert exported_rows[0]["emotion_text"] == "export me"
    assert owner_id != other_id

    export_csv = api_client.post(
        "/api/emotions/exports/",
        {
            "file_format": "csv",
            "start_at": "2026-05-15T00:00:00+08:00",
            "end_at": "2026-05-15T23:59:59+08:00",
        },
        format="json",
        **auth_headers,
    )
    assert export_csv.status_code == 201
    csv_content = export_csv.json()["data"]["content"]
    assert "export me" in csv_content
    assert "other user's note" not in csv_content

    task_id = export_json.json()["data"]["id"]
    owner_download = api_client.get(f"/api/emotions/exports/{task_id}/download/", **auth_headers)
    assert owner_download.status_code == 200
    assert owner_download.json()["data"]["record_count"] == 1

    forbidden_download = api_client.get(
        f"/api/emotions/exports/{task_id}/download/",
        HTTP_AUTHORIZATION=f"Bearer {other_token}",
    )
    assert forbidden_download.status_code == 404
