from __future__ import annotations

import base64
import hashlib
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


ENCRYPTED_PREFIX = "enc::v1::"


class EncryptionConfigurationError(Exception):
    pass


class EncryptionOperationError(Exception):
    pass


@lru_cache(maxsize=1)
def get_fernet() -> Fernet:
    key = (settings.FIELD_ENCRYPTION_KEY or "").strip()
    if not key:
        if not settings.FIELD_ENCRYPTION_ALLOW_FALLBACK:
            raise EncryptionConfigurationError("Field encryption key is not configured.")
        key = _derive_fallback_key(str(settings.SECRET_KEY))
    return Fernet(key.encode("ascii"))


def encrypt_text(value: str) -> str:
    plain_text = value or ""
    if plain_text == "":
        return ""
    try:
        encrypted = get_fernet().encrypt(plain_text.encode("utf-8")).decode("utf-8")
    except EncryptionConfigurationError:
        raise
    except Exception as exc:
        raise EncryptionOperationError("Failed to encrypt emotion text.") from exc
    return f"{ENCRYPTED_PREFIX}{encrypted}"


def decrypt_text(value: str, *, is_encrypted: bool) -> str:
    if not value:
        return ""
    if not is_encrypted:
        return value
    if not value.startswith(ENCRYPTED_PREFIX):
        return value
    token = value[len(ENCRYPTED_PREFIX) :]
    try:
        return get_fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except EncryptionConfigurationError:
        raise
    except InvalidToken as exc:
        raise EncryptionOperationError("Failed to decrypt emotion text.") from exc
    except Exception as exc:
        raise EncryptionOperationError("Failed to decrypt emotion text.") from exc


def prepare_text_for_storage(value: str, *, encrypt: bool) -> str:
    return encrypt_text(value or "") if encrypt else (value or "")


def is_encrypted_payload(value: str) -> bool:
    return bool(value) and str(value).startswith(ENCRYPTED_PREFIX)


def _derive_fallback_key(secret_key: str) -> str:
    digest = hashlib.sha256(secret_key.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii")
