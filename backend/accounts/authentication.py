from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication

from .models import AdminUser
from .token_utils import JWTExpiredError, JWTTokenError, decode_admin_token


class AdminJWTAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != self.keyword.lower():
            raise exceptions.AuthenticationFailed("Invalid authorization header.")

        token = parts[1]
        try:
            payload = decode_admin_token(token)
        except JWTExpiredError as exc:
            raise exceptions.AuthenticationFailed("Admin token expired.") from exc
        except JWTTokenError as exc:
            raise exceptions.AuthenticationFailed("Invalid admin token.") from exc

        try:
            admin_user = AdminUser.objects.get(pk=payload["sub"])
        except AdminUser.DoesNotExist as exc:
            raise exceptions.AuthenticationFailed("Admin user not found.") from exc

        if not admin_user.is_active:
            raise exceptions.AuthenticationFailed("Admin user is disabled.")

        return admin_user, token
