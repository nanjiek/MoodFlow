from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CompanionContentViewSet, SystemConfigViewSet


router = DefaultRouter()
router.register("companion-contents", CompanionContentViewSet, basename="companion-content")
router.register("system-configs", SystemConfigViewSet, basename="system-config")

urlpatterns = [
    path("", include(router.urls)),
]
