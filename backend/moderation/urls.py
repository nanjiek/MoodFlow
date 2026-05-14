from django.urls import path

from .views import (
    TreeHolePostApproveView,
    TreeHolePostDetailView,
    TreeHolePostListView,
    TreeHolePostRejectView,
)


app_name = "moderation"

urlpatterns = [
    path("posts/", TreeHolePostListView.as_view(), name="tree-hole-post-list"),
    path("posts/<int:pk>/", TreeHolePostDetailView.as_view(), name="tree-hole-post-detail"),
    path("posts/<int:pk>/approve/", TreeHolePostApproveView.as_view(), name="tree-hole-post-approve"),
    path("posts/<int:pk>/reject/", TreeHolePostRejectView.as_view(), name="tree-hole-post-reject"),
]
