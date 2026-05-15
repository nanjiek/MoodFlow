from django.urls import path, re_path

from .views import (
    PasswordResetSendCodeView,
    PasswordResetVerifyCodeView,
    PasswordResetView,
    SocialLoginStateView,
    SocialLoginView,
    UserLoginView,
    UserLogoutView,
    UserPrivacyView,
    UserProfileView,
    UserRegisterView,
    UserSocialBindingView,
    UserSocialUnbindView,
)


urlpatterns = [
    re_path(r"^auth/register/?$", UserRegisterView.as_view(), name="user-auth-register"),
    re_path(r"^auth/login/?$", UserLoginView.as_view(), name="user-auth-login"),
    re_path(r"^auth/logout/?$", UserLogoutView.as_view(), name="user-auth-logout"),
    re_path(r"^auth/social/(?P<provider>wechat|qq)/state/?$", SocialLoginStateView.as_view(), name="user-auth-social-state"),
    re_path(r"^auth/social/(?P<provider>wechat|qq)/login/?$", SocialLoginView.as_view(), name="user-auth-social-login"),
    re_path(r"^auth/password-reset/send-code/?$", PasswordResetSendCodeView.as_view(), name="user-auth-password-reset-send-code"),
    re_path(r"^auth/password-reset/verify-code/?$", PasswordResetVerifyCodeView.as_view(), name="user-auth-password-reset-verify-code"),
    re_path(r"^auth/password-reset/reset/?$", PasswordResetView.as_view(), name="user-auth-password-reset"),
    path("me/", UserProfileView.as_view(), name="user-profile"),
    path("me/privacy/", UserPrivacyView.as_view(), name="user-privacy"),
    path("me/social-bindings/", UserSocialBindingView.as_view(), name="user-social-bindings"),
    path("me/social-bindings/<int:binding_id>/", UserSocialUnbindView.as_view(), name="user-social-unbind"),
]
