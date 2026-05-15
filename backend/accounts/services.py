from __future__ import annotations

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils import timezone

from emotions.models import AppUser

from .models import PhoneVerificationCode, UserSocialAccount

INVALID_PASSWORD_RESET_REQUEST_MESSAGE = "Invalid or expired password reset request."


@dataclass
class SocialIdentity:
    provider: str
    open_id: str
    union_id: str = ""
    app_id: str = ""
    nickname: str = ""
    avatar_url: str = ""
    profile_snapshot: dict | None = None


def issue_social_login_state(provider: str) -> dict[str, str]:
    normalized_provider = _normalize_provider(provider)
    state = secrets.token_urlsafe(24)
    expires_at = timezone.now() + timedelta(seconds=settings.SOCIAL_LOGIN_STATE_TTL_SECONDS)
    cache.set(_social_state_cache_key(normalized_provider, state), "1", timeout=settings.SOCIAL_LOGIN_STATE_TTL_SECONDS)
    return {
        "provider": normalized_provider,
        "state": state,
        "expires_at": expires_at.isoformat(),
    }


def consume_social_login_state(provider: str, state: str) -> None:
    normalized_provider = _normalize_provider(provider)
    cache_key = _social_state_cache_key(normalized_provider, state or "")
    if not state or not cache.get(cache_key):
        raise ValidationError({"state": "Invalid or expired social login state."})
    cache.delete(cache_key)


def resolve_social_identity(provider: str, payload: dict) -> SocialIdentity:
    normalized_provider = _normalize_provider(provider)
    open_id = str(payload.get("mock_open_id") or payload.get("open_id") or "").strip()
    union_id = str(payload.get("union_id") or "").strip()
    nickname = str(payload.get("nickname") or "").strip()
    avatar_url = str(payload.get("avatar_url") or "").strip()

    if settings.SOCIAL_LOGIN_MOCK_MODE and open_id:
        return SocialIdentity(
            provider=normalized_provider,
            open_id=open_id,
            union_id=union_id,
            app_id=_provider_app_id(normalized_provider),
            nickname=nickname,
            avatar_url=avatar_url,
            profile_snapshot=_compact_payload(payload),
        )

    auth_code = str(payload.get("auth_code") or "").strip()
    if auth_code and _provider_is_configured(normalized_provider):
        raise ValidationError(
            {
                "auth_code": (
                    "Real OAuth exchange requires platform callback integration and credentials; "
                    "use mock_open_id locally until the provider is configured."
                )
            }
        )

    raise ValidationError(
        {
            "open_id": "Provide mock_open_id/open_id in local mode, or complete real provider OAuth configuration."
        }
    )


def login_or_register_social_user(identity: SocialIdentity) -> tuple[AppUser, UserSocialAccount, bool]:
    binding = (
        UserSocialAccount.objects.select_related("user")
        .filter(provider=identity.provider, open_id=identity.open_id)
        .order_by("id")
        .first()
    )
    created = False
    if binding is None:
        created = True
        user = AppUser.objects.create(
            external_id=f"{identity.provider}:{identity.open_id}",
            nickname=identity.nickname or f"{identity.provider}_user",
            avatar_url=identity.avatar_url,
            is_active=True,
        )
        binding = UserSocialAccount.objects.create(
            user=user,
            provider=identity.provider,
            open_id=identity.open_id,
            union_id=identity.union_id,
            app_id=identity.app_id,
            nickname=identity.nickname,
            avatar_url=identity.avatar_url,
            profile_snapshot=identity.profile_snapshot or {},
            last_login_at=timezone.now(),
        )
    else:
        user = binding.user
        updates = []
        if identity.nickname and user.nickname != identity.nickname:
            user.nickname = identity.nickname
            updates.append("nickname")
        if identity.avatar_url and user.avatar_url != identity.avatar_url:
            user.avatar_url = identity.avatar_url
            updates.append("avatar_url")
        if updates:
            updates.append("updated_at")
            user.save(update_fields=updates)
        _update_social_binding(binding, identity, last_login=True)

    if not user.is_active:
        raise ValidationError({"detail": "User is disabled."})
    return user, binding, created


def bind_social_account(user: AppUser, identity: SocialIdentity) -> UserSocialAccount:
    existing = UserSocialAccount.objects.filter(provider=identity.provider, open_id=identity.open_id).first()
    if existing and existing.user_id != user.id:
        raise ValidationError({"open_id": "This social account is already linked to another user."})
    if existing:
        _update_social_binding(existing, identity, last_login=False)
        return existing

    return UserSocialAccount.objects.create(
        user=user,
        provider=identity.provider,
        open_id=identity.open_id,
        union_id=identity.union_id,
        app_id=identity.app_id,
        nickname=identity.nickname,
        avatar_url=identity.avatar_url,
        profile_snapshot=identity.profile_snapshot or {},
    )


def send_password_reset_code(*, phone: str, request_ip: str = "") -> dict[str, object]:
    normalized_phone = str(phone or "").strip()
    user = AppUser.objects.filter(phone=normalized_phone).order_by("id").first()
    _enforce_password_reset_rate_limit(normalized_phone, request_ip)
    code = _generate_verification_code()
    request_id = uuid.uuid4().hex
    expires_at = timezone.now() + timedelta(seconds=settings.PASSWORD_RESET_CODE_TTL_SECONDS)
    PhoneVerificationCode.objects.create(
        phone=normalized_phone,
        purpose=PhoneVerificationCode.Purpose.PASSWORD_RESET,
        request_id=request_id,
        code_hash=_hash_verification_code(code),
        expires_at=expires_at,
        max_attempts=settings.PASSWORD_RESET_CODE_MAX_ATTEMPTS,
        metadata={"request_ip": request_ip, "user_exists": user is not None},
    )
    payload = {
        "request_id": request_id,
        "expires_at": expires_at.isoformat(),
        "phone": normalized_phone,
        "cooldown_seconds": settings.PASSWORD_RESET_SEND_COOLDOWN_SECONDS,
    }
    if settings.PASSWORD_RESET_EXPOSE_DEBUG_CODE:
        payload["debug_code"] = code
    return payload


def verify_password_reset_code(*, phone: str, request_id: str, code: str, consume: bool = False) -> PhoneVerificationCode:
    verification = _get_password_reset_verification(phone=phone, request_id=request_id)
    if verification.consumed_at is not None:
        raise ValidationError({"code": "Verification code has already been used."})
    if verification.expires_at <= timezone.now():
        raise ValidationError({"code": "Verification code has expired."})
    if verification.attempt_count >= verification.max_attempts:
        raise ValidationError({"code": "Verification code attempt limit exceeded."})
    if verification.code_hash != _hash_verification_code(code):
        verification.attempt_count += 1
        verification.save(update_fields=["attempt_count", "updated_at"])
        raise ValidationError({"code": "Invalid verification code."})

    update_fields = []
    if verification.verified_at is None:
        verification.verified_at = timezone.now()
        update_fields.append("verified_at")
    if consume:
        verification.consumed_at = timezone.now()
        update_fields.append("consumed_at")
    if update_fields:
        update_fields.append("updated_at")
        verification.save(update_fields=update_fields)
    return verification


def reset_user_password(*, phone: str, request_id: str, code: str, new_password: str) -> AppUser:
    verification = verify_password_reset_code(phone=phone, request_id=request_id, code=code, consume=True)
    if not verification.metadata.get("user_exists", False):
        raise ValidationError({"detail": INVALID_PASSWORD_RESET_REQUEST_MESSAGE})
    user = AppUser.objects.filter(phone=str(phone or "").strip()).order_by("id").first()
    if user is None:
        raise ValidationError({"detail": INVALID_PASSWORD_RESET_REQUEST_MESSAGE})
    user.set_password(new_password)
    user.save(update_fields=["password_hash"])
    return user


def _get_password_reset_verification(*, phone: str, request_id: str) -> PhoneVerificationCode:
    verification = (
        PhoneVerificationCode.objects.filter(
            phone=str(phone or "").strip(),
            request_id=str(request_id or "").strip(),
            purpose=PhoneVerificationCode.Purpose.PASSWORD_RESET,
        )
        .order_by("-created_at", "-id")
        .first()
    )
    if verification is None:
        raise ValidationError({"detail": INVALID_PASSWORD_RESET_REQUEST_MESSAGE})
    return verification


def _hash_verification_code(code: str) -> str:
    raw = f"{settings.SECRET_KEY}:{str(code or '').strip()}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _generate_verification_code() -> str:
    debug_code = (settings.PASSWORD_RESET_DEBUG_CODE or "").strip()
    if debug_code:
        return debug_code
    return f"{secrets.randbelow(1000000):06d}"


def _enforce_password_reset_rate_limit(phone: str, request_ip: str) -> None:
    cooldown_key = f"accounts:password-reset:cooldown:{phone}"
    if cache.get(cooldown_key):
        raise ValidationError({"phone": "Verification code sent too frequently. Please try again later."})

    daily_key = f"accounts:password-reset:daily:{phone}:{timezone.localdate().isoformat()}"
    daily_count = cache.get(daily_key, 0)
    if daily_count >= settings.PASSWORD_RESET_DAILY_LIMIT:
        raise ValidationError({"phone": "Daily verification code limit reached."})

    ip_key = f"accounts:password-reset:ip:{request_ip}:{timezone.localdate().isoformat()}" if request_ip else ""
    if ip_key:
        ip_count = cache.get(ip_key, 0)
        if ip_count >= settings.PASSWORD_RESET_DAILY_LIMIT * 3:
            raise ValidationError({"detail": "Too many verification code requests from this IP."})
        cache.set(ip_key, ip_count + 1, timeout=24 * 60 * 60)

    cache.set(cooldown_key, 1, timeout=settings.PASSWORD_RESET_SEND_COOLDOWN_SECONDS)
    cache.set(daily_key, daily_count + 1, timeout=24 * 60 * 60)


def _normalize_provider(provider: str) -> str:
    normalized = str(provider or "").strip().lower()
    supported = {choice for choice, _ in UserSocialAccount.Provider.choices}
    if normalized not in supported:
        raise ValidationError({"provider": "Unsupported social provider."})
    return normalized


def _provider_is_configured(provider: str) -> bool:
    if provider == UserSocialAccount.Provider.WECHAT:
        return bool(settings.WECHAT_APP_ID and settings.WECHAT_APP_SECRET)
    if provider == UserSocialAccount.Provider.QQ:
        return bool(settings.QQ_APP_ID and settings.QQ_APP_SECRET)
    return False


def _provider_app_id(provider: str) -> str:
    if provider == UserSocialAccount.Provider.WECHAT:
        return settings.WECHAT_APP_ID or "wechat-mock-app"
    if provider == UserSocialAccount.Provider.QQ:
        return settings.QQ_APP_ID or "qq-mock-app"
    return ""


def _social_state_cache_key(provider: str, state: str) -> str:
    return f"accounts:social-state:{provider}:{state}"


def _compact_payload(payload: dict) -> dict:
    return {
        key: value
        for key, value in payload.items()
        if key in {"auth_code", "open_id", "mock_open_id", "union_id", "nickname", "avatar_url"}
    }


def _update_social_binding(binding: UserSocialAccount, identity: SocialIdentity, *, last_login: bool) -> None:
    update_fields = []
    for field_name, value in (
        ("union_id", identity.union_id),
        ("app_id", identity.app_id),
        ("nickname", identity.nickname),
        ("avatar_url", identity.avatar_url),
    ):
        if value and getattr(binding, field_name) != value:
            setattr(binding, field_name, value)
            update_fields.append(field_name)
    if identity.profile_snapshot:
        binding.profile_snapshot = identity.profile_snapshot
        update_fields.append("profile_snapshot")
    if last_login:
        binding.last_login_at = timezone.now()
        update_fields.append("last_login_at")
    if update_fields:
        update_fields.append("updated_at")
        binding.save(update_fields=update_fields)
