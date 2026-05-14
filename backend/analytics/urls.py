from django.urls import re_path

from .views import (
    ActiveUsersStatisticsView,
    AdminOperationLogListView,
    EmotionDistributionStatisticsView,
    FeatureUsageStatisticsView,
    OverviewStatisticsView,
)


app_name = "analytics"


def statistics_urlpatterns(prefix="", name_prefix="analytics"):
    return [
        re_path(
            rf"^{prefix}overview/?$",
            OverviewStatisticsView.as_view(),
            name=f"{name_prefix}-overview",
        ),
        re_path(
            rf"^{prefix}active-users/?$",
            ActiveUsersStatisticsView.as_view(),
            name=f"{name_prefix}-active-users",
        ),
        re_path(
            rf"^{prefix}emotion-distribution/?$",
            EmotionDistributionStatisticsView.as_view(),
            name=f"{name_prefix}-emotion-distribution",
        ),
        re_path(
            rf"^{prefix}feature-usage/?$",
            FeatureUsageStatisticsView.as_view(),
            name=f"{name_prefix}-feature-usage",
        ),
        re_path(
            rf"^{prefix}operation-logs/?$",
            AdminOperationLogListView.as_view(),
            name=f"{name_prefix}-operation-logs",
        ),
    ]

urlpatterns = [
    *statistics_urlpatterns("", "admin-statistics"),
]
