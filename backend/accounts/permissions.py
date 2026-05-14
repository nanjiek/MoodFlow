from rest_framework.permissions import BasePermission

from .models import AdminUser
from emotions.models import AppUser


class IsAdminAuthenticated(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return isinstance(user, AdminUser) and user.is_active


class IsAppUserAuthenticated(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return isinstance(user, AppUser) and user.is_active
