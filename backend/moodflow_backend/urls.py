"""URL configuration for MoodFlow."""

from __future__ import annotations

from importlib.util import find_spec

from django.contrib import admin
from django.urls import include, path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from common.response import APIResponse


def module_exists(module_name: str) -> bool:
    try:
        return find_spec(module_name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    return APIResponse.success(
        data={
            "status": "ok",
            "service": "moodflow-backend",
        }
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="health-check"),
]

ADMIN_APP_MOUNTS = [
    ("accounts.urls", "api/admin/auth/"),
    ("emotions.urls", "api/admin/emotions/"),
    ("content.urls", "api/admin/content/"),
    ("moderation.urls", "api/admin/tree-hole/"),
    ("analytics.urls", "api/admin/statistics/"),
    ("mlops.urls", "api/admin/mlops/"),
]

for urls_module, route_prefix in ADMIN_APP_MOUNTS:
    if module_exists(urls_module):
        urlpatterns.append(path(route_prefix, include(urls_module)))
