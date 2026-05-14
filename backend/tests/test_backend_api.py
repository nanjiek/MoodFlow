from __future__ import annotations

import pytest


pytest.importorskip("django")
pytest.importorskip("pytest_django")
pytest.importorskip("rest_framework")

from django.urls import NoReverseMatch, reverse
from rest_framework.test import APIClient

from accounts.models import AdminUser


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


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
