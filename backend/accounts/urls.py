from django.urls import re_path

from .views import AdminLoginView, AdminLogoutView, AdminProfileView

app_name = "accounts"

urlpatterns = [
    re_path(r"^login/?$", AdminLoginView.as_view(), name="admin-auth-login"),
    re_path(r"^logout/?$", AdminLogoutView.as_view(), name="admin-auth-logout"),
    re_path(r"^profile/?$", AdminProfileView.as_view(), name="admin-auth-profile"),
]
