from __future__ import annotations

import pytest


pytest.importorskip("django")
pytest.importorskip("pytest_django")
pytest.importorskip("rest_framework")

from django.core.cache import cache
from rest_framework.test import APIClient

from emotions.models import AppUser


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture(autouse=True)
def clear_cache(settings):
    settings.PASSWORD_RESET_DEBUG_CODE = "246810"
    settings.PASSWORD_RESET_EXPOSE_DEBUG_CODE = True
    cache.clear()
    yield
    cache.clear()


def _issue_social_state(api_client: APIClient, provider: str) -> str:
    response = api_client.post(f"/api/auth/social/{provider}/state/", format="json")
    assert response.status_code == 200
    return response.json()["data"]["state"]


@pytest.mark.django_db
def test_social_login_auto_registers_and_reuses_binding(api_client: APIClient) -> None:
    first_state = _issue_social_state(api_client, "wechat")
    first_response = api_client.post(
        "/api/auth/social/wechat/login/",
        {
            "state": first_state,
            "mock_open_id": "wx-open-001",
            "nickname": "WeChat User",
            "avatar_url": "https://example.com/a.png",
        },
        format="json",
    )
    assert first_response.status_code == 200
    first_payload = first_response.json()["data"]
    assert first_payload["is_first_login"] is True
    assert first_payload["profile"]["nickname"] == "WeChat User"
    user_id = first_payload["profile"]["id"]

    second_state = _issue_social_state(api_client, "wechat")
    second_response = api_client.post(
        "/api/auth/social/wechat/login/",
        {
            "state": second_state,
            "mock_open_id": "wx-open-001",
            "nickname": "WeChat User Updated",
        },
        format="json",
    )
    assert second_response.status_code == 200
    second_payload = second_response.json()["data"]
    assert second_payload["is_first_login"] is False
    assert second_payload["profile"]["id"] == user_id

    user = AppUser.objects.get(pk=user_id)
    assert user.nickname == "WeChat User Updated"


@pytest.mark.django_db
def test_social_login_requires_valid_state_and_supports_binding(api_client: APIClient) -> None:
    invalid_state_response = api_client.post(
        "/api/auth/social/qq/login/",
        {"state": "bad-state", "mock_open_id": "qq-open-fail"},
        format="json",
    )
    assert invalid_state_response.status_code == 400

    register_response = api_client.post(
        "/api/auth/register/",
        {"phone": "13810101010", "password": "MoodFlowUser123!", "nickname": "Phone User"},
        format="json",
    )
    token = register_response.json()["data"]["token"]
    state = _issue_social_state(api_client, "qq")
    bind_response = api_client.post(
        "/api/me/social-bindings/",
        {"provider": "qq", "state": state, "mock_open_id": "qq-open-001", "nickname": "QQ User"},
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert bind_response.status_code == 200
    assert bind_response.json()["data"]["provider"] == "qq"

    other_register = api_client.post(
        "/api/auth/register/",
        {"phone": "13810101011", "password": "MoodFlowUser123!", "nickname": "Other User"},
        format="json",
    )
    other_token = other_register.json()["data"]["token"]
    second_state = _issue_social_state(api_client, "qq")
    conflict_response = api_client.post(
        "/api/me/social-bindings/",
        {"provider": "qq", "state": second_state, "mock_open_id": "qq-open-001"},
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {other_token}",
    )
    assert conflict_response.status_code == 400


@pytest.mark.django_db
def test_password_reset_verify_and_reset_with_attempt_limit(api_client: APIClient) -> None:
    register_response = api_client.post(
        "/api/auth/register/",
        {"phone": "13820202020", "password": "OldPassword123!", "nickname": "Reset User"},
        format="json",
    )
    assert register_response.status_code == 201

    send_response = api_client.post(
        "/api/auth/password-reset/send-code/",
        {"phone": "13820202020"},
        format="json",
    )
    assert send_response.status_code == 200
    send_payload = send_response.json()["data"]

    bad_verify = api_client.post(
        "/api/auth/password-reset/verify-code/",
        {"phone": "13820202020", "request_id": send_payload["request_id"], "code": "000001"},
        format="json",
    )
    assert bad_verify.status_code == 400

    good_verify = api_client.post(
        "/api/auth/password-reset/verify-code/",
        {
            "phone": "13820202020",
            "request_id": send_payload["request_id"],
            "code": send_payload["debug_code"],
        },
        format="json",
    )
    assert good_verify.status_code == 200
    assert good_verify.json()["data"]["verified"] is True

    reset_response = api_client.post(
        "/api/auth/password-reset/reset/",
        {
            "phone": "13820202020",
            "request_id": send_payload["request_id"],
            "code": send_payload["debug_code"],
            "new_password": "NewPassword123!",
        },
        format="json",
    )
    assert reset_response.status_code == 200

    login_response = api_client.post(
        "/api/auth/login/",
        {"phone": "13820202020", "password": "NewPassword123!"},
        format="json",
    )
    assert login_response.status_code == 200

    other_user = api_client.post(
        "/api/auth/register/",
        {"phone": "13820202021", "password": "OriginPass123!", "nickname": "Locked User"},
        format="json",
    )
    assert other_user.status_code == 201
    locked_send = api_client.post(
        "/api/auth/password-reset/send-code/",
        {"phone": "13820202021"},
        format="json",
    )
    locked_payload = locked_send.json()["data"]
    for _ in range(5):
        response = api_client.post(
            "/api/auth/password-reset/verify-code/",
            {"phone": "13820202021", "request_id": locked_payload["request_id"], "code": "999999"},
            format="json",
        )
    assert response.status_code == 400

    locked_reset = api_client.post(
        "/api/auth/password-reset/reset/",
        {
            "phone": "13820202021",
            "request_id": locked_payload["request_id"],
            "code": locked_payload["debug_code"],
            "new_password": "AnotherPass123!",
        },
        format="json",
    )
    assert locked_reset.status_code == 400


@pytest.mark.django_db
def test_password_reset_send_code_does_not_expose_phone_existence(api_client: APIClient) -> None:
    response = api_client.post(
        "/api/auth/password-reset/send-code/",
        {"phone": "13820209999"},
        format="json",
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["phone"] == "13820209999"
    assert payload["request_id"]
    assert payload["debug_code"] == "246810"


@pytest.mark.django_db
def test_password_reset_reset_returns_generic_success_for_unknown_phone(api_client: APIClient) -> None:
    send_response = api_client.post(
        "/api/auth/password-reset/send-code/",
        {"phone": "13820208888"},
        format="json",
    )
    payload = send_response.json()["data"]

    reset_response = api_client.post(
        "/api/auth/password-reset/reset/",
        {
            "phone": "13820208888",
            "request_id": payload["request_id"],
            "code": payload["debug_code"],
            "new_password": "AnotherPass123!",
        },
        format="json",
    )
    assert reset_response.status_code == 400
    payload = reset_response.json()
    assert payload["message"] == "validation error"
    assert payload["data"]["detail"] == ["Invalid or expired password reset request."]


@pytest.mark.django_db
def test_password_reset_debug_code_can_be_disabled(api_client: APIClient, settings) -> None:
    settings.PASSWORD_RESET_EXPOSE_DEBUG_CODE = False

    api_client.post(
        "/api/auth/register/",
        {"phone": "13820202029", "password": "OldPassword123!", "nickname": "No Debug"},
        format="json",
    )
    response = api_client.post(
        "/api/auth/password-reset/send-code/",
        {"phone": "13820202029"},
        format="json",
    )
    assert response.status_code == 200
    assert "debug_code" not in response.json()["data"]
