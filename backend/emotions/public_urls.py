from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    UserDeviceTokenView,
    UserEmotionAnalysisCorrectView,
    UserEmotionDailyReportView,
    UserEmotionExportDownloadView,
    UserEmotionExportView,
    UserEmotionGrowthCurveView,
    UserEmotionRecordViewSet,
    UserEmotionWeeklyReportView,
    UserReminderPreferenceView,
    UserReminderTriggerView,
)


router = DefaultRouter()
router.register("records", UserEmotionRecordViewSet, basename="user-emotion-record")

urlpatterns = [
    path("emotions/", include(router.urls)),
    path("emotions/reports/daily/", UserEmotionDailyReportView.as_view(), name="user-emotion-daily-report"),
    path("emotions/reports/weekly/", UserEmotionWeeklyReportView.as_view(), name="user-emotion-weekly-report"),
    path("emotions/growth-curve/", UserEmotionGrowthCurveView.as_view(), name="user-emotion-growth-curve"),
    path("emotions/analyses/<int:analysis_pk>/correct/", UserEmotionAnalysisCorrectView.as_view(), name="user-emotion-analysis-correct"),
    path("emotions/devices/", UserDeviceTokenView.as_view(), name="user-emotion-device-tokens"),
    path("emotions/reminder-preferences/", UserReminderPreferenceView.as_view(), name="user-emotion-reminder-preferences"),
    path("emotions/reminders/trigger/", UserReminderTriggerView.as_view(), name="user-emotion-reminder-trigger"),
    path("emotions/exports/", UserEmotionExportView.as_view(), name="user-emotion-export"),
    path("emotions/exports/<int:task_id>/download/", UserEmotionExportDownloadView.as_view(), name="user-emotion-export-download"),
]
