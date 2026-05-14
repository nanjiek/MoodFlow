from django.db.models import Q
from rest_framework import serializers

from .models import AdminUser


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
