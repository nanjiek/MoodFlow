from __future__ import annotations

from datetime import datetime, time, timedelta

import pytest


pytest.importorskip("django")
pytest.importorskip("pytest_django")
pytest.importorskip("rest_framework")

from django.utils import timezone
from rest_framework.test import APIClient

from analytics.models import FeatureUsageLog
from content.models import CompanionContent
from emotions.models import AppUser, EmotionAnalysis, EmotionRecord, EmotionTag


@pytest.fixture
def user_client() -> tuple[APIClient, AppUser]:
    user = AppUser.objects.create(external_id="user-growth-001", nickname="Curve Tester")
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user


@pytest.mark.django_db
def test_companion_recommendations_use_latest_analysis_and_log_view(user_client: tuple[APIClient, AppUser]) -> None:
    client, user = user_client
    anxious = EmotionTag.objects.create(code="anxious", name="Anxious", sort_order=10, is_active=True)
    calm = EmotionTag.objects.create(code="calm", name="Calm", sort_order=20, is_active=True)

    record = EmotionRecord.objects.create(
        user=user,
        emotion_text="Tomorrow's demo is making me tense.",
        tag=calm,
        recorded_at=timezone.now() - timedelta(hours=1),
    )
    EmotionAnalysis.objects.create(
        record=record,
        predicted_label="anxious",
        confidence=0.91,
        keywords=["demo", "tense"],
        intensity=7,
        trend=EmotionAnalysis.TREND_RISING,
    )

    anxious_item = CompanionContent.objects.create(
        emotion_tag=anxious,
        content_type=CompanionContent.CONTENT_TYPE_BREATHING,
        title="4-6 breathing",
        body="Breathe with a slower exhale.",
        weight=10,
        is_active=True,
    )
    CompanionContent.objects.create(
        emotion_tag=None,
        content_type=CompanionContent.CONTENT_TYPE_PHRASE,
        title="Small step",
        body="Focus on the next small step only.",
        weight=1,
        is_active=True,
    )

    response = client.get("/api/companion/recommendations/?limit=2")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["emotion"]["code"] == "anxious"
    assert payload["emotion_source"] == "latest_analysis"
    assert payload["recommendations"][0]["id"] == anxious_item.id

    usage_log = FeatureUsageLog.objects.get(feature="companion_recommendations")
    assert usage_log.action == "view"
    assert usage_log.user_id == str(user.id)
    assert usage_log.metadata["emotion"] == "anxious"


@pytest.mark.django_db
def test_growth_curve_supports_drilldown_and_logs_usage(user_client: tuple[APIClient, AppUser]) -> None:
    client, user = user_client
    happy = EmotionTag.objects.create(code="happy", name="Happy", sort_order=10, is_active=True)
    tired = EmotionTag.objects.create(code="tired", name="Tired", sort_order=20, is_active=True)

    today = timezone.localdate()
    yesterday = today - timedelta(days=1)
    yesterday_record = EmotionRecord.objects.create(
        user=user,
        emotion_text="Wrapped up a hard task.",
        tag=happy,
        recorded_at=timezone.make_aware(datetime.combine(yesterday, time(9, 0)), timezone.get_current_timezone()),
    )
    EmotionAnalysis.objects.create(
        record=yesterday_record,
        predicted_label="happy",
        confidence=0.88,
        keywords=["wrapped", "task"],
        intensity=6,
        trend=EmotionAnalysis.TREND_STABLE,
    )

    today_record = EmotionRecord.objects.create(
        user=user,
        emotion_text="Running low on energy today.",
        tag=tired,
        recorded_at=timezone.make_aware(datetime.combine(today, time(20, 30)), timezone.get_current_timezone()),
        is_collect=True,
    )
    EmotionAnalysis.objects.create(
        record=today_record,
        predicted_label="tired",
        confidence=0.83,
        keywords=["energy"],
        intensity=8,
        trend=EmotionAnalysis.TREND_FALLING,
    )

    response = client.get(f"/api/emotions/growth-curve/?days=7&date={today.isoformat()}")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["summary"]["record_count"] == 2
    assert len(payload["series"]) == 7
    assert payload["drilldown"]["date"] == today.isoformat()
    assert payload["drilldown"]["record_count"] == 1
    assert payload["drilldown"]["records"][0]["id"] == today_record.id

    usage_log = FeatureUsageLog.objects.get(feature="emotion_growth_curve")
    assert usage_log.action == "drilldown_view"
    assert usage_log.user_id == str(user.id)
    assert usage_log.metadata["drilldown_date"] == today.isoformat()


@pytest.mark.django_db
def test_history_by_day_endpoint_returns_records_and_logs_view(user_client: tuple[APIClient, AppUser]) -> None:
    client, user = user_client
    plain = EmotionTag.objects.create(code="plain", name="Plain", sort_order=10, is_active=True)
    target_day = timezone.localdate()

    morning_record = EmotionRecord.objects.create(
        user=user,
        emotion_text="A normal morning.",
        tag=plain,
        recorded_at=timezone.make_aware(datetime.combine(target_day, time(8, 15)), timezone.get_current_timezone()),
    )
    EmotionRecord.objects.create(
        user=user,
        emotion_text="Yesterday note.",
        tag=plain,
        recorded_at=timezone.make_aware(
            datetime.combine(target_day - timedelta(days=1), time(22, 0)),
            timezone.get_current_timezone(),
        ),
    )

    response = client.get(f"/api/emotions/records/history-by-day/?date={target_day.isoformat()}")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["date"] == target_day.isoformat()
    assert payload["count"] == 1
    assert payload["results"][0]["id"] == morning_record.id

    usage_log = FeatureUsageLog.objects.get(feature="emotion_history_by_day")
    assert usage_log.action == "view"
    assert usage_log.user_id == str(user.id)
    assert usage_log.metadata["date"] == target_day.isoformat()
