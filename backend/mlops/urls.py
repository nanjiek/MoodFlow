from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import InferenceLogViewSet, ModelStatusView, ModelVersionViewSet, TrainingSampleViewSet


app_name = "mlops"

router = DefaultRouter()
router.register("samples", TrainingSampleViewSet, basename="training-sample")
router.register("model-versions", ModelVersionViewSet, basename="model-version")
router.register("inference-logs", InferenceLogViewSet, basename="inference-log")

urlpatterns = [
    path("", include(router.urls)),
    path("status/", ModelStatusView.as_view(), name="model-status"),
]
