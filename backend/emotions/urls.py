from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AppUserViewSet, EmotionAnalysisByRecordView, EmotionAnalysisViewSet, EmotionRecordViewSet, EmotionTagViewSet

app_name = "emotions"

router = DefaultRouter()
router.register("users", AppUserViewSet, basename="app-user")
router.register("tags", EmotionTagViewSet, basename="emotion-tag")
router.register("records", EmotionRecordViewSet, basename="emotion-record")
router.register("analyses", EmotionAnalysisViewSet, basename="emotion-analysis")

urlpatterns = [
    path("", include(router.urls)),
    path("records/<int:record_pk>/analysis/", EmotionAnalysisByRecordView.as_view(), name="record-analysis"),
]
