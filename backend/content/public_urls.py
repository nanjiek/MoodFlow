from django.urls import re_path

from .views import CompanionRecommendationsView


urlpatterns = [
    re_path(r"^companion/recommendations/?$", CompanionRecommendationsView.as_view(), name="user-companion-recommendations"),
]
