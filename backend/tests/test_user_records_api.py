from __future__ import annotations

import pytest


pytest.importorskip("django")
pytest.importorskip("pytest_django")
pytest.importorskip("rest_framework")

from rest_framework.test import APIClient

from emotions.models import AppUser, EmotionAnalysis, EmotionRecord, EmotionTag


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def auth_headers(api_client: APIClient) -> dict[str, str]:
    response = api_client.post(
        "/api/auth/register/",
        {
            "phone": "13600136000",
            "password": "MoodFlowUser123!",
            "nickname": "记录用户",
        },
        format="json",
    )
    assert response.status_code == 201
    token = response.json()["data"]["token"]
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def emotion_tags() -> dict[str, EmotionTag]:
    return {
        "happy": EmotionTag.objects.create(code="happy", name="开心", sort_order=10, is_active=True),
        "tired": EmotionTag.objects.create(code="tired", name="疲惫", sort_order=20, is_active=True),
        "sad": EmotionTag.objects.create(code="sad", name="难过", sort_order=30, is_active=True),
    }


@pytest.fixture
def stub_prediction(monkeypatch):
    def fake_call_model_service(text: str, selected_label: str | None = None):
        label = selected_label or "plain"
        return {
            "label": label,
            "label_name": label,
            "display_name": label,
            "display_hint": label,
            "category": "neutral",
            "confidence": 0.91,
            "intensity": 0.7,
            "keywords": [label, "记录"],
            "explanation": f"analysis for {label}",
            "gentle_feedback": "take care",
            "recommended_content_types": ["phrase"],
            "suggested_prompt": "prompt",
            "model_version": "test-suite",
            "probabilities": {label: 0.91},
        }

    monkeypatch.setattr("emotions.views.call_model_service", fake_call_model_service)


@pytest.mark.django_db
def test_user_record_crud_favorite_and_record_analysis(
    api_client: APIClient,
    auth_headers: dict[str, str],
    emotion_tags: dict[str, EmotionTag],
    stub_prediction,
) -> None:
    create_response = api_client.post(
        "/api/emotions/records/",
        {
            "selected_label": emotion_tags["happy"].code,
            "emoji_id": "smile-1",
            "is_collect": False,
            "is_encrypted": True,
            "recorded_at": "2026-05-14T09:30:00+08:00",
        },
        format="json",
        **auth_headers,
    )

    assert create_response.status_code == 201
    create_payload = create_response.json()["data"]
    record_id = create_payload["id"]
    assert create_payload["text"] == ""
    assert create_payload["selected_label"] == "happy"
    assert create_payload["emoji_id"] == "smile-1"
    assert create_payload["is_encrypted"] is True
    assert create_payload["analysis"]["predicted_label"] == "happy"

    record = EmotionRecord.objects.get(pk=record_id)
    assert record.emotion_text == ""
    analysis = EmotionAnalysis.objects.get(record=record)
    assert analysis.model_version == "test-suite"
    assert analysis.intensity == 7

    list_response = api_client.get("/api/emotions/records/", **auth_headers)
    assert list_response.status_code == 200
    assert list_response.json()["data"]["results"][0]["id"] == record_id

    update_response = api_client.patch(
        f"/api/emotions/records/{record_id}/",
        {
            "selected_label": emotion_tags["tired"].code,
            "text": "今天电量有点低",
            "is_collect": True,
        },
        format="json",
        **auth_headers,
    )
    assert update_response.status_code == 200
    update_payload = update_response.json()["data"]
    assert update_payload["selected_label"] == "tired"
    assert update_payload["text"] == "今天电量有点低"
    assert update_payload["is_collect"] is True
    assert update_payload["analysis"]["predicted_label"] == "tired"

    toggle_response = api_client.post(
        f"/api/emotions/records/{record_id}/toggle-collect/",
        format="json",
        **auth_headers,
    )
    assert toggle_response.status_code == 200
    assert toggle_response.json()["data"]["is_collect"] is False

    analysis_response = api_client.get(
        f"/api/emotions/records/{record_id}/analysis/",
        **auth_headers,
    )
    assert analysis_response.status_code == 200
    analysis_payload = analysis_response.json()["data"]
    assert analysis_payload["record_id"] == record_id
    assert analysis_payload["selected_label"] == "tired"
    assert analysis_payload["predicted_label"] == "tired"

    delete_response = api_client.delete(
        f"/api/emotions/records/{record_id}/",
        **auth_headers,
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["data"]["deleted"] is True
    assert EmotionRecord.objects.filter(pk=record_id).exists() is False
    assert EmotionAnalysis.objects.filter(record_id=record_id).exists() is False


@pytest.mark.django_db
def test_user_record_reports_and_analysis_correction(
    api_client: APIClient,
    auth_headers: dict[str, str],
    emotion_tags: dict[str, EmotionTag],
    stub_prediction,
) -> None:
    user = AppUser.objects.get(phone="13600136000")
    today_record = EmotionRecord.objects.create(
        user=user,
        emotion_text="今天有点累",
        tag=emotion_tags["tired"],
        is_collect=True,
        recorded_at="2026-05-14T08:00:00+08:00",
    )
    today_analysis = EmotionAnalysis.objects.create(
        record=today_record,
        predicted_label="tired",
        confidence=0.88,
        keywords=["累", "今天"],
        intensity=8,
        trend=EmotionAnalysis.TREND_RISING,
        cause="分析结果 A",
        model_version="test-suite",
        raw_result={"label": "tired"},
    )
    EmotionRecord.objects.create(
        user=user,
        emotion_text="昨天心情不错",
        tag=emotion_tags["happy"],
        recorded_at="2026-05-13T20:00:00+08:00",
    )

    daily_response = api_client.get(
        "/api/emotions/reports/daily/?date=2026-05-14",
        **auth_headers,
    )
    assert daily_response.status_code == 200
    daily_payload = daily_response.json()["data"]
    assert daily_payload["date"] == "2026-05-14"
    assert daily_payload["total_records"] == 1
    assert daily_payload["collect_count"] == 1
    assert daily_payload["dominant_emotion"]["code"] == "tired"

    weekly_response = api_client.get(
        "/api/emotions/reports/weekly/?start_date=2026-05-13&end_date=2026-05-14",
        **auth_headers,
    )
    assert weekly_response.status_code == 200
    weekly_payload = weekly_response.json()["data"]
    assert weekly_payload["start_date"] == "2026-05-13"
    assert weekly_payload["end_date"] == "2026-05-14"
    assert weekly_payload["total_records"] == 2
    assert len(weekly_payload["daily_series"]) >= 2
    assert "summary" in weekly_payload["summary"]

    correct_response = api_client.post(
        f"/api/emotions/analyses/{today_analysis.id}/correct/",
        {"accepted": False, "corrected_label": emotion_tags["sad"].code, "note": "更像情绪低落"},
        format="json",
        **auth_headers,
    )
    assert correct_response.status_code == 200
    correct_payload = correct_response.json()["data"]
    assert correct_payload["feedback_saved"] is True
    assert correct_payload["feedback"]["corrected_label"] == "sad"

    today_analysis.refresh_from_db()
    assert today_analysis.raw_result["user_feedback"]["corrected_label"] == "sad"
