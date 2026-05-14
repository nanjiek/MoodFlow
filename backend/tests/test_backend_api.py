from __future__ import annotations

import pytest


pytest.importorskip("django")
pytest.importorskip("pytest_django")
pytest.importorskip("rest_framework")

from django.urls import NoReverseMatch, reverse
from rest_framework.test import APIClient

from accounts.models import AdminUser
from analytics.models import FeatureUsageLog
from emotions.models import AppUser, EmotionAnalysis, EmotionRecord, EmotionTag


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def admin_token(api_client: APIClient) -> str:
    raw_password = "MoodFlowAdmin123!"
    admin_user = AdminUser(
        username="admin_suite",
        email="admin-suite@example.com",
        role=AdminUser.Role.SUPER_ADMIN,
        status=AdminUser.Status.ACTIVE,
    )
    admin_user.set_password(raw_password)
    admin_user.save()

    login_url = _reverse_or_path(
        "accounts:admin-auth-login",
        "/api/admin/auth/login/",
    )
    response = api_client.post(
        login_url,
        {"username": admin_user.username, "password": raw_password},
        format="json",
    )
    assert response.status_code == 200
    return response.json()["token"]


def _reverse_or_path(route_name: str, fallback: str) -> str:
    try:
        return reverse(route_name)
    except NoReverseMatch:
        return fallback


def test_health_check_returns_ok(api_client: APIClient) -> None:
    response = api_client.get("/api/health/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    assert payload["data"]["status"] == "ok"
    assert payload["data"]["service"] == "moodflow-backend"


@pytest.mark.django_db
def test_admin_login_flow_returns_token_and_allows_profile(api_client: APIClient) -> None:
    raw_password = "MoodFlowAdmin123!"
    admin_user = AdminUser(
        username="admin_flow",
        email="admin-flow@example.com",
        role=AdminUser.Role.SUPER_ADMIN,
        status=AdminUser.Status.ACTIVE,
    )
    admin_user.set_password(raw_password)
    admin_user.save()

    login_url = _reverse_or_path(
        "accounts:admin-auth-login",
        "/api/admin/auth/login/",
    )
    login_response = api_client.post(
        login_url,
        {"username": admin_user.username, "password": raw_password},
        format="json",
    )

    assert login_response.status_code == 200
    login_payload = login_response.json()
    assert login_payload["token_type"] == "Bearer"
    assert login_payload["token"]
    assert login_payload["profile"]["username"] == admin_user.username

    admin_user.refresh_from_db()
    assert admin_user.last_login_at is not None

    profile_url = _reverse_or_path(
        "accounts:admin-auth-profile",
        "/api/admin/auth/profile/",
    )
    profile_response = api_client.get(
        profile_url,
        HTTP_AUTHORIZATION=f"Bearer {login_payload['token']}",
    )

    assert profile_response.status_code == 200
    assert profile_response.json()["username"] == admin_user.username


@pytest.mark.django_db
def test_emotion_record_guide_and_weekly_summary(admin_token: str, api_client: APIClient) -> None:
    happy = EmotionTag.objects.create(code="happy", name="开心", sort_order=10, is_active=True)
    anxious = EmotionTag.objects.create(code="anxious", name="焦虑", sort_order=20, is_active=True)
    user = AppUser.objects.create(external_id="user-001", nickname="小满")

    first_record = EmotionRecord.objects.create(
        user=user,
        emotion_text="今天完成了一个重要任务",
        tag=happy,
    )
    EmotionAnalysis.objects.create(
        record=first_record,
        predicted_label="happy",
        confidence=0.82,
        keywords=["完成", "任务"],
        intensity=6,
        trend=EmotionAnalysis.TREND_STABLE,
        cause="今天完成了重要任务，所以整体比较开心。",
    )

    second_record = EmotionRecord.objects.create(
        user=user,
        emotion_text="明天要汇报，心里一直很慌",
        tag=anxious,
    )
    EmotionAnalysis.objects.create(
        record=second_record,
        predicted_label="anxious",
        confidence=0.88,
        keywords=["汇报", "很慌"],
        intensity=8,
        trend=EmotionAnalysis.TREND_RISING,
    )

    guide_response = api_client.get(
        "/api/admin/emotions/records/guide/",
        HTTP_AUTHORIZATION=f"Bearer {admin_token}",
    )
    assert guide_response.status_code == 200
    guide_payload = guide_response.json()["data"]
    assert guide_payload["target_duration_seconds"] == 30
    assert guide_payload["text_optional"] is True
    assert len(guide_payload["guided_prompts"]) >= 1

    summary_response = api_client.get(
        f"/api/admin/emotions/records/weekly-summary/?user_id={user.id}",
        HTTP_AUTHORIZATION=f"Bearer {admin_token}",
    )
    assert summary_response.status_code == 200
    summary_payload = summary_response.json()["data"]
    assert "summary" in summary_payload
    assert summary_payload["dominant_emotion"]["code"] in {"happy", "anxious"}
    assert len(summary_payload["highlights"]) >= 1


@pytest.mark.django_db
def test_emotion_analysis_correction_logs_feedback(admin_token: str, api_client: APIClient) -> None:
    anxious = EmotionTag.objects.create(code="anxious", name="焦虑", sort_order=20, is_active=True)
    tired = EmotionTag.objects.create(code="tired", name="疲惫", sort_order=30, is_active=True)
    user = AppUser.objects.create(external_id="user-002", nickname="阿川")
    record = EmotionRecord.objects.create(
        user=user,
        emotion_text="最近加班很多，整个人像没电了一样",
        tag=anxious,
    )
    analysis = EmotionAnalysis.objects.create(
        record=record,
        predicted_label="anxious",
        confidence=0.67,
        keywords=["加班", "没电"],
        intensity=8,
        trend=EmotionAnalysis.TREND_RISING,
    )

    response = api_client.post(
        f"/api/admin/emotions/analyses/{analysis.id}/correct/",
        {"accepted": False, "corrected_label": tired.code, "note": "更像疲惫，不是焦虑"},
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {admin_token}",
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["feedback_saved"] is True
    assert payload["feedback"]["corrected_label"] == "tired"

    analysis.refresh_from_db()
    assert analysis.raw_result["user_feedback"]["corrected_label"] == "tired"
    assert FeatureUsageLog.objects.filter(feature="emotion_analysis", action="correction_submitted").exists()
