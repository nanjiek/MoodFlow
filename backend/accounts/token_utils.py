import base64
import binascii
import hashlib
import hmac
import json
from datetime import timedelta

from django.conf import settings
from django.utils import timezone


JWT_ALGORITHM = "HS256"
JWT_EXPIRES_IN = timedelta(hours=24)


class JWTTokenError(Exception):
    pass


class JWTExpiredError(JWTTokenError):
    pass


def create_admin_token(admin_user):
    now = timezone.now()
    expires_at = now + JWT_EXPIRES_IN
    payload = {
        "sub": str(admin_user.pk),
        "username": admin_user.username,
        "role": admin_user.role,
        "token_type": "admin",
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return encode_jwt(payload), expires_at


def decode_admin_token(token):
    payload = decode_jwt(token)
    if payload.get("token_type") != "admin":
        raise JWTTokenError("Invalid token type.")
    if not payload.get("sub"):
        raise JWTTokenError("Missing subject.")
    return payload


def encode_jwt(payload):
    header = {"typ": "JWT", "alg": JWT_ALGORITHM}
    encoded_header = _base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    encoded_payload = _base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{encoded_header}.{encoded_payload}"
    signature = _sign(signing_input)
    return f"{signing_input}.{signature}"


def decode_jwt(token):
    try:
        encoded_header, encoded_payload, encoded_signature = token.split(".")
    except ValueError as exc:
        raise JWTTokenError("Invalid token format.") from exc

    signing_input = f"{encoded_header}.{encoded_payload}"
    expected_signature = _sign(signing_input)
    if not hmac.compare_digest(encoded_signature, expected_signature):
        raise JWTTokenError("Invalid token signature.")

    try:
        header = json.loads(_base64url_decode(encoded_header))
        payload = json.loads(_base64url_decode(encoded_payload))
    except (TypeError, ValueError, binascii.Error) as exc:
        raise JWTTokenError("Invalid token payload.") from exc

    if header.get("alg") != JWT_ALGORITHM:
        raise JWTTokenError("Unsupported token algorithm.")

    exp = payload.get("exp")
    if exp is None:
        raise JWTTokenError("Missing expiration.")
    try:
        expires_at = int(exp)
    except (TypeError, ValueError) as exc:
        raise JWTTokenError("Invalid expiration.") from exc
    if timezone.now().timestamp() >= expires_at:
        raise JWTExpiredError("Token expired.")

    return payload


def _sign(signing_input):
    secret = str(settings.SECRET_KEY).encode("utf-8")
    digest = hmac.new(secret, signing_input.encode("ascii"), hashlib.sha256).digest()
    return _base64url_encode(digest)


def _base64url_encode(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _base64url_decode(encoded):
    padding = "=" * (-len(encoded) % 4)
    return base64.urlsafe_b64decode(f"{encoded}{padding}".encode("ascii"))
