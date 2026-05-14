from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from common.response import APIResponse

from .audit import log_admin_operation
from .authentication import AdminJWTAuthentication, UserJWTAuthentication
from .permissions import IsAdminAuthenticated, IsAppUserAuthenticated
from .serializers import (
    AdminLoginSerializer,
    AdminProfileSerializer,
    UserLoginSerializer,
    UserPrivacySerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    UserRegisterSerializer,
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


def _request_value(request, key):
    data = getattr(request, "data", {})
    if hasattr(data, "get"):
        return data.get(key, "")
    return ""
