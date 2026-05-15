from django.contrib.auth.hashers import check_password as django_check_password
from django.contrib.auth.hashers import make_password
from django.db import models


class AdminUser(models.Model):
    class Role(models.TextChoices):
        SUPER_ADMIN = "super_admin", "Super Admin"
        ADMIN = "admin", "Admin"
        OPERATOR = "operator", "Operator"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        DISABLED = "disabled", "Disabled"

    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=128)
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.ADMIN)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.ACTIVE)
    last_login_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "admin_users"
        ordering = ["-created_at"]

    def __str__(self):
        return self.username

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return django_check_password(raw_password, self.password_hash)


class UserSocialAccount(models.Model):
    class Provider(models.TextChoices):
        WECHAT = "wechat", "WeChat"
        QQ = "qq", "QQ"

    user = models.ForeignKey("emotions.AppUser", related_name="social_accounts", on_delete=models.CASCADE)
    provider = models.CharField(max_length=16, choices=Provider.choices, db_index=True)
    open_id = models.CharField(max_length=128)
    union_id = models.CharField(max_length=128, blank=True)
    app_id = models.CharField(max_length=128, blank=True)
    nickname = models.CharField(max_length=64, blank=True)
    avatar_url = models.URLField(max_length=500, blank=True)
    profile_snapshot = models.JSONField(default=dict, blank=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_user_social_account"
        ordering = ("provider", "id")
        constraints = [
            models.UniqueConstraint(fields=("provider", "open_id"), name="acct_soc_provider_oid_uq"),
        ]
        indexes = (
            models.Index(fields=("user", "provider"), name="acct_soc_user_prov_idx"),
            models.Index(fields=("provider", "union_id"), name="acct_soc_prov_union_idx"),
        )

    def __str__(self):
        return f"{self.provider}:{self.open_id}"


class PhoneVerificationCode(models.Model):
    class Purpose(models.TextChoices):
        PASSWORD_RESET = "password_reset", "Password Reset"

    phone = models.CharField(max_length=32, db_index=True)
    purpose = models.CharField(max_length=32, choices=Purpose.choices, db_index=True)
    request_id = models.CharField(max_length=64, unique=True)
    code_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField(db_index=True)
    max_attempts = models.PositiveSmallIntegerField(default=5)
    attempt_count = models.PositiveSmallIntegerField(default=0)
    send_count = models.PositiveSmallIntegerField(default=1)
    verified_at = models.DateTimeField(null=True, blank=True)
    consumed_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_phone_verification_code"
        ordering = ("-created_at", "-id")
        indexes = (
            models.Index(fields=("phone", "purpose", "created_at"), name="acct_verify_phone_purp_idx"),
            models.Index(fields=("purpose", "expires_at"), name="acct_verify_purp_exp_idx"),
        )

    def __str__(self):
        return f"{self.phone}:{self.purpose}:{self.request_id}"
