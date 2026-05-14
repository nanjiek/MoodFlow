from django.urls import path, re_path

from .views import (
    UserLoginView,
    UserLogoutView,
    UserPrivacyView,
    UserProfileView,
    UserRegisterView,
)


urlpatterns = [
    re_path(r"^auth/register/?$", UserRegisterView.as_view(), name="user-auth-register"),
    re_path(r"^auth/login/?$", UserLoginView.as_view(), name="user-auth-login"),
    re_path(r"^auth/logout/?$", UserLogoutView.as_view(), name="user-auth-logout"),
    path("me/", UserProfileView.as_view(), name="user-profile"),
    path("me/privacy/", UserPrivacyView.as_view(), name="user-privacy"),
]
