from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    UserEmotionAnalysisCorrectView,
    UserEmotionDailyReportView,
    UserEmotionGrowthCurveView,
    UserEmotionRecordViewSet,
    UserEmotionWeeklyReportView,
)


router = DefaultRouter()
router.register("records", UserEmotionRecordViewSet, basename="user-emotion-record")

urlpatterns = [
    path("emotions/", include(router.urls)),
    path("emotions/reports/daily/", UserEmotionDailyReportView.as_view(), name="user-emotion-daily-report"),
    path("emotions/reports/weekly/", UserEmotionWeeklyReportView.as_view(), name="user-emotion-weekly-report"),
    path("emotions/growth-curve/", UserEmotionGrowthCurveView.as_view(), name="user-emotion-growth-curve"),
    path("emotions/analyses/<int:analysis_pk>/correct/", UserEmotionAnalysisCorrectView.as_view(), name="user-emotion-analysis-correct"),
]
