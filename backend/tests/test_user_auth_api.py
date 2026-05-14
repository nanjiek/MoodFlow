from __future__ import annotations

import pytest


pytest.importorskip("django")
pytest.importorskip("pytest_django")
pytest.importorskip("rest_framework")

from rest_framework.test import APIClient

from accounts.models import AdminUser
from emotions.models import AppUser


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.mark.django_db
def test_user_register_login_profile_and_privacy_flow(api_client: APIClient) -> None:
    register_response = api_client.post(
        "/api/auth/register/",
        {"phone": "13800138000", "password": "MoodFlowUser123!", "nickname": "小满"},
        format="json",
    )

    assert register_response.status_code == 201
    register_payload = register_response.json()["data"]
    assert register_payload["token_type"] == "Bearer"
    assert register_payload["profile"]["phone"] == "13800138000"
    assert register_payload["profile"]["privacy"] == {
        "anonymous_mode": False,
        "emotion_encryption_enabled": False,
    }

    app_user = AppUser.objects.get(phone="13800138000")
    assert app_user.nickname == "小满"
    assert app_user.check_password("MoodFlowUser123!")

    me_response = api_client.get(
        "/api/me/",
        HTTP_AUTHORIZATION=f"Bearer {register_payload['token']}",
    )
    assert me_response.status_code == 200
    assert me_response.json()["data"]["nickname"] == "小满"

    profile_update_response = api_client.patch(
        "/api/me/",
        {
            "nickname": "新小满",
            "gender": AppUser.GENDER_FEMALE,
            "email": "user@example.com",
            "signature": "愿今天轻一点。",
        },
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {register_payload['token']}",
    )
    assert profile_update_response.status_code == 200
    assert profile_update_response.json()["data"]["nickname"] == "新小满"
    assert profile_update_response.json()["data"]["signature"] == "愿今天轻一点。"

    privacy_response = api_client.get(
        "/api/me/privacy/",
        HTTP_AUTHORIZATION=f"Bearer {register_payload['token']}",
    )
    assert privacy_response.status_code == 200
    assert privacy_response.json()["data"] == {
        "anonymous_mode": False,
        "emotion_encryption_enabled": False,
    }

    privacy_update_response = api_client.patch(
        "/api/me/privacy/",
        {"anonymous_mode": True, "emotion_encryption_enabled": True},
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {register_payload['token']}",
    )
    assert privacy_update_response.status_code == 200
    assert privacy_update_response.json()["data"] == {
        "anonymous_mode": True,
        "emotion_encryption_enabled": True,
    }

    login_response = api_client.post(
        "/api/auth/login/",
        {"phone": "13800138000", "password": "MoodFlowUser123!"},
        format="json",
    )
    assert login_response.status_code == 200
    login_payload = login_response.json()["data"]
    assert login_payload["profile"]["nickname"] == "新小满"

    logout_response = api_client.post(
        "/api/auth/logout/",
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {login_payload['token']}",
    )
    assert logout_response.status_code == 200
    assert logout_response.json()["data"]["detail"] == "Logged out."


@pytest.mark.django_db
def test_user_and_admin_jwts_are_isolated(api_client: APIClient) -> None:
    app_user = AppUser.objects.create(
        external_id="user-iso-001",
        nickname="阿川",
        phone="13900139000",
        is_active=True,
    )
    app_user.set_password("MoodFlowUser123!")
    app_user.save(update_fields=["password_hash"])

    user_login_response = api_client.post(
        "/api/auth/login/",
        {"phone": "13900139000", "password": "MoodFlowUser123!"},
        format="json",
    )
    assert user_login_response.status_code == 200
    user_token = user_login_response.json()["data"]["token"]

    admin_password = "MoodFlowAdmin123!"
    admin_user = AdminUser(
        username="admin_isolation",
        email="admin-isolation@example.com",
        role=AdminUser.Role.SUPER_ADMIN,
        status=AdminUser.Status.ACTIVE,
    )
    admin_user.set_password(admin_password)
    admin_user.save()

    admin_login_response = api_client.post(
        "/api/admin/auth/login/",
        {"username": admin_user.username, "password": admin_password},
        format="json",
    )
    assert admin_login_response.status_code == 200
    admin_token = admin_login_response.json()["token"]

    me_with_admin_token = api_client.get(
        "/api/me/",
        HTTP_AUTHORIZATION=f"Bearer {admin_token}",
    )
    assert me_with_admin_token.status_code in {401, 403}

    admin_profile_with_user_token = api_client.get(
        "/api/admin/auth/profile/",
        HTTP_AUTHORIZATION=f"Bearer {user_token}",
    )
    assert admin_profile_with_user_token.status_code in {401, 403}


@pytest.mark.django_db
def test_user_register_rejects_duplicate_phone(api_client: APIClient) -> None:
    existing_user = AppUser.objects.create(
        external_id="user-dup-001",
        nickname="已有用户",
        phone="13700137000",
        is_active=True,
    )
    existing_user.set_password("MoodFlowUser123!")
    existing_user.save(update_fields=["password_hash"])

    duplicate_response = api_client.post(
        "/api/auth/register/",
        {"phone": "13700137000", "password": "MoodFlowUser123!", "nickname": "重复用户"},
        format="json",
    )

    assert duplicate_response.status_code == 400
    assert "phone" in duplicate_response.json()["data"]
