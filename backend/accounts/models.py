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
