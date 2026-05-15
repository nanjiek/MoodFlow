from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from common.response import APIResponse

from .audit import log_admin_operation
from .authentication import AdminJWTAuthentication, UserJWTAuthentication
from .permissions import IsAdminAuthenticated, IsAppUserAuthenticated
from .services import (
    bind_social_account,
    consume_social_login_state,
    issue_social_login_state,
    login_or_register_social_user,
    reset_user_password,
    resolve_social_identity,
    send_password_reset_code,
    verify_password_reset_code,
)
from .serializers import (
    AdminLoginSerializer,
    AdminProfileSerializer,
    PasswordResetResetSerializer,
    PasswordResetSendSerializer,
    PasswordResetVerifySerializer,
    SocialLoginSerializer,
    UserLoginSerializer,
    UserPrivacySerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    UserRegisterSerializer,
    UserSocialAccountSerializer,
)
from .token_utils import create_admin_token, create_user_token


class AdminLoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            log_admin_operation(
                None,
                "login_failed",
                request=request,
                detail="Admin login failed.",
                metadata={"username": _request_value(request, "username")},
            )
            raise

        admin_user = serializer.validated_data["admin_user"]
        admin_user.last_login_at = timezone.now()
        admin_user.save(update_fields=["last_login_at", "updated_at"])

        token, expires_at = create_admin_token(admin_user)
        log_admin_operation(
            admin_user,
            "login",
            request=request,
            detail="Admin login succeeded.",
            metadata={"username": admin_user.username},
        )

        return Response(
            {
                "token": token,
                "token_type": "Bearer",
                "expires_at": expires_at.isoformat(),
                "profile": AdminProfileSerializer(admin_user).data,
            },
            status=status.HTTP_200_OK,
        )


class AdminLogoutView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAdminAuthenticated]

    def post(self, request):
        log_admin_operation(
            request.user,
            "logout",
            request=request,
            detail="Admin logout succeeded.",
            metadata={"username": request.user.username},
        )
        return Response({"detail": "Logged out."}, status=status.HTTP_200_OK)


class AdminProfileView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAdminAuthenticated]

    def get(self, request):
        return Response(AdminProfileSerializer(request.user).data, status=status.HTTP_200_OK)


class UserRegisterView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, expires_at = create_user_token(user)
        return APIResponse.success(
            data={
                "token": token,
                "token_type": "Bearer",
                "expires_at": expires_at.isoformat(),
                "profile": UserProfileSerializer(user).data,
            },
            status_code=status.HTTP_201_CREATED,
        )


class UserLoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["app_user"]
        token, expires_at = create_user_token(user)
        return APIResponse.success(
            data={
                "token": token,
                "token_type": "Bearer",
                "expires_at": expires_at.isoformat(),
                "profile": UserProfileSerializer(user).data,
            }
        )


class UserLogoutView(APIView):
    authentication_classes = [UserJWTAuthentication]
    permission_classes = [IsAppUserAuthenticated]

    def post(self, request):
        return APIResponse.success(data={"detail": "Logged out."})


class UserProfileView(APIView):
    authentication_classes = [UserJWTAuthentication]
    permission_classes = [IsAppUserAuthenticated]

    def get(self, request):
        return APIResponse.success(data=UserProfileSerializer(request.user).data)

    def patch(self, request):
        serializer = UserProfileUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return APIResponse.success(data=UserProfileSerializer(request.user).data)


class UserPrivacyView(APIView):
    authentication_classes = [UserJWTAuthentication]
    permission_classes = [IsAppUserAuthenticated]

    def get(self, request):
        return APIResponse.success(data=UserPrivacySerializer(request.user).data)

    def patch(self, request):
        serializer = UserPrivacySerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return APIResponse.success(data=UserPrivacySerializer(request.user).data)


class SocialLoginStateView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, provider):
        return APIResponse.success(data=issue_social_login_state(provider))


class SocialLoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, provider):
        serializer = SocialLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        consume_social_login_state(provider, serializer.validated_data["state"])
        identity = resolve_social_identity(provider, serializer.validated_data)
        user, binding, created = login_or_register_social_user(identity)
        token, expires_at = create_user_token(user)
        return APIResponse.success(
            data={
                "token": token,
                "token_type": "Bearer",
                "expires_at": expires_at.isoformat(),
                "profile": UserProfileSerializer(user).data,
                "social_account": UserSocialAccountSerializer(binding).data,
                "is_first_login": created,
            }
        )


class UserSocialBindingView(APIView):
    authentication_classes = [UserJWTAuthentication]
    permission_classes = [IsAppUserAuthenticated]

    def get(self, request):
        bindings = request.user.social_accounts.all().order_by("provider", "id")
        return APIResponse.success(data=UserSocialAccountSerializer(bindings, many=True).data)

    def post(self, request):
        provider = request.data.get("provider", "")
        serializer = SocialLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        consume_social_login_state(provider, serializer.validated_data["state"])
        identity = resolve_social_identity(provider, serializer.validated_data)
        binding = bind_social_account(request.user, identity)
        return APIResponse.success(data=UserSocialAccountSerializer(binding).data, message="bound")


class UserSocialUnbindView(APIView):
    authentication_classes = [UserJWTAuthentication]
    permission_classes = [IsAppUserAuthenticated]

    def delete(self, request, binding_id):
        binding = request.user.social_accounts.filter(pk=binding_id).first()
        if binding is None:
            raise ValidationError({"binding_id": "Social binding does not exist."})
        binding.delete()
        return APIResponse.success(data={"id": binding_id, "deleted": True}, message="unbound")


class PasswordResetSendCodeView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = PasswordResetSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = send_password_reset_code(
            phone=serializer.validated_data["phone"],
            request_ip=_client_ip(request),
        )
        return APIResponse.success(data=payload, message="code sent")


class PasswordResetVerifyCodeView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = PasswordResetVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        verification = verify_password_reset_code(
            phone=serializer.validated_data["phone"],
            request_id=serializer.validated_data["request_id"],
            code=serializer.validated_data["code"],
            consume=False,
        )
        return APIResponse.success(
            data={
                "request_id": verification.request_id,
                "phone": verification.phone,
                "verified": True,
                "expires_at": verification.expires_at.isoformat(),
            },
            message="verified",
        )


class PasswordResetView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = PasswordResetResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = reset_user_password(
            phone=serializer.validated_data["phone"],
            request_id=serializer.validated_data["request_id"],
            code=serializer.validated_data["code"],
            new_password=serializer.validated_data["new_password"],
        )
        return APIResponse.success(data={"user_id": user.id, "password_reset": True}, message="password reset")


def _request_value(request, key):
    data = getattr(request, "data", {})
    if hasattr(data, "get"):
        return data.get(key, "")
    return ""


def _client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")
