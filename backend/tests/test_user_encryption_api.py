from __future__ import annotations

import pytest


pytest.importorskip("django")
pytest.importorskip("pytest_django")
pytest.importorskip("rest_framework")

from rest_framework.test import APIClient

from emotions.models import EmotionAnalysis, EmotionRecord, EmotionTag


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def auth_headers(api_client: APIClient) -> dict[str, str]:
    response = api_client.post(
        "/api/auth/register/",
        {"phone": "13840404040", "password": "MoodFlowUser123!", "nickname": "Encrypted User"},
        format="json",
    )
    token = response.json()["data"]["token"]
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def happy_tag() -> EmotionTag:
    return EmotionTag.objects.create(code="happy", name="Happy", sort_order=10, is_active=True)


@pytest.fixture
def capture_prediction(monkeypatch):
    captured = {}

    def fake_call_model_service(text: str, selected_label: str | None = None):
        captured["text"] = text
        captured["selected_label"] = selected_label
        return {
            "label": selected_label or "happy",
            "confidence": 0.9,
            "intensity": 0.6,
            "keywords": ["secure", "text"],
            "explanation": "captured",
            "model_version": "encrypt-suite",
        }

    monkeypatch.setattr("emotions.views.call_model_service", fake_call_model_service)
    return captured


@pytest.mark.django_db
def test_encrypted_record_create_read_update_and_analysis(
    api_client: APIClient,
    auth_headers: dict[str, str],
    happy_tag: EmotionTag,
    capture_prediction,
) -> None:
    create_response = api_client.post(
        "/api/emotions/records/",
        {
            "selected_label": happy_tag.code,
            "text": "private note",
            "is_encrypted": True,
            "recorded_at": "2026-05-15T09:00:00+08:00",
        },
        format="json",
        **auth_headers,
    )
    assert create_response.status_code == 201
    create_payload = create_response.json()["data"]
    record_id = create_payload["id"]
    assert create_payload["text"] == "private note"
    assert capture_prediction["text"] == "private note"

    record = EmotionRecord.objects.get(pk=record_id)
    assert record.emotion_text != "private note"
    assert record.emotion_text.startswith("enc::v1::")

    retrieve_response = api_client.get(f"/api/emotions/records/{record_id}/", **auth_headers)
    assert retrieve_response.status_code == 200
    assert retrieve_response.json()["data"]["text"] == "private note"

    update_response = api_client.patch(
        f"/api/emotions/records/{record_id}/",
        {
            "selected_label": happy_tag.code,
            "text": "updated secret",
            "is_encrypted": True,
        },
        format="json",
        **auth_headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["text"] == "updated secret"
    assert capture_prediction["text"] == "updated secret"

    record.refresh_from_db()
    assert record.emotion_text != "updated secret"
    analysis = EmotionAnalysis.objects.get(record=record)
    assert analysis.model_version == "encrypt-suite"

    analysis_response = api_client.get(f"/api/emotions/records/{record_id}/analysis/", **auth_headers)
    assert analysis_response.status_code == 200
    assert analysis_response.json()["data"]["record_id"] == record_id


@pytest.mark.django_db
def test_encrypted_record_plaintext_is_returned_in_growth_drilldown(
    api_client: APIClient,
    auth_headers: dict[str, str],
    happy_tag: EmotionTag,
    capture_prediction,
) -> None:
    create_response = api_client.post(
        "/api/emotions/records/",
        {
            "selected_label": happy_tag.code,
            "text": "drilldown secret",
            "is_encrypted": True,
            "recorded_at": "2026-05-15T14:00:00+08:00",
        },
        format="json",
        **auth_headers,
    )
    assert create_response.status_code == 201

    growth_response = api_client.get(
        "/api/emotions/growth-curve/?date=2026-05-15&days=7",
        **auth_headers,
    )
    assert growth_response.status_code == 200
    drilldown_records = growth_response.json()["data"]["drilldown"]["records"]
    assert drilldown_records[0]["emotion_text"] == "drilldown secret"
