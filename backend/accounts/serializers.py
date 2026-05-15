from django.db.models import Q
from rest_framework import serializers

from emotions.models import AppUser

from .models import AdminUser, UserSocialAccount


class AdminProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminUser
        fields = [
            "id",
            "username",
            "email",
            "role",
            "status",
            "last_login_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class AdminLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    default_error_messages = {
        "invalid_credentials": "Invalid username or password.",
        "disabled": "Admin user is disabled.",
    }

    def validate(self, attrs):
        identifier = attrs["username"].strip()
        password = attrs["password"]

        admin_user = (
            AdminUser.objects.filter(Q(username=identifier) | Q(email=identifier))
            .order_by("id")
            .first()
        )
        if admin_user is None or not admin_user.check_password(password):
            self.fail("invalid_credentials")
        if not admin_user.is_active:
            self.fail("disabled")

        attrs["admin_user"] = admin_user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    privacy = serializers.SerializerMethodField()
    social_accounts = serializers.SerializerMethodField()

    class Meta:
        model = AppUser
        fields = (
            "id",
            "external_id",
            "nickname",
            "avatar_url",
            "gender",
            "birth_date",
            "phone",
            "email",
            "signature",
            "anonymous_mode",
            "emotion_encryption_enabled",
            "privacy",
            "social_accounts",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "phone")

    def get_privacy(self, obj):
        return {
            "anonymous_mode": obj.anonymous_mode,
            "emotion_encryption_enabled": obj.emotion_encryption_enabled,
        }

    def get_social_accounts(self, obj):
        accounts = getattr(obj, "social_accounts", None)
        if accounts is None:
            accounts = obj.social_accounts.all()
        return UserSocialAccountSerializer(accounts, many=True).data


class UserPrivacySerializer(serializers.ModelSerializer):
    class Meta:
        model = AppUser
        fields = ("anonymous_mode", "emotion_encryption_enabled")


class UserRegisterSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)
    password = serializers.CharField(min_length=6, max_length=128, trim_whitespace=False, write_only=True)
    nickname = serializers.CharField(max_length=64)

    default_error_messages = {
        "phone_exists": "This phone number is already registered.",
    }

    def validate_phone(self, value):
        normalized = str(value).strip()
        if AppUser.objects.filter(phone=normalized).exclude(phone="").exists():
            self.fail("phone_exists")
        return normalized

    def create(self, validated_data):
        user = AppUser(
            phone=validated_data["phone"],
            nickname=validated_data["nickname"].strip(),
            external_id=validated_data["phone"],
            is_active=True,
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    default_error_messages = {
        "invalid_credentials": "Invalid phone or password.",
        "disabled": "User is disabled.",
    }

    def validate(self, attrs):
        phone = attrs["phone"].strip()
        password = attrs["password"]
        app_user = AppUser.objects.filter(phone=phone).order_by("id").first()
        if app_user is None or not app_user.check_password(password):
            self.fail("invalid_credentials")
        if not app_user.is_active:
            self.fail("disabled")
        attrs["app_user"] = app_user
        attrs["phone"] = phone
        return attrs


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppUser
        fields = ("nickname", "avatar_url", "gender", "birth_date", "email", "signature")


class UserSocialAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSocialAccount
        fields = (
            "id",
            "provider",
            "open_id",
            "union_id",
            "app_id",
            "nickname",
            "avatar_url",
            "last_login_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class SocialLoginSerializer(serializers.Serializer):
    state = serializers.CharField(max_length=128)
    auth_code = serializers.CharField(required=False, allow_blank=True)
    open_id = serializers.CharField(required=False, allow_blank=True)
    mock_open_id = serializers.CharField(required=False, allow_blank=True)
    union_id = serializers.CharField(required=False, allow_blank=True)
    nickname = serializers.CharField(required=False, allow_blank=True, max_length=64)
    avatar_url = serializers.URLField(required=False, allow_blank=True)


class PasswordResetSendSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)

    def validate_phone(self, value):
        return str(value).strip()


class PasswordResetVerifySerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)
    request_id = serializers.CharField(max_length=64)
    code = serializers.CharField(max_length=12)

    def validate_phone(self, value):
        return str(value).strip()


class PasswordResetResetSerializer(PasswordResetVerifySerializer):
    new_password = serializers.CharField(min_length=6, max_length=128, trim_whitespace=False, write_only=True)
