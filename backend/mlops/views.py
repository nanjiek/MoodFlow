from django.db import transaction
from django.db.models import Count, Max
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from common.pagination import StandardResultsSetPagination

from .models import InferenceLog, ModelVersion, TrainingSample
from .serializers import (
    CorrectTrainingSampleSerializer,
    IgnoreTrainingSampleSerializer,
    InferenceLogSerializer,
    ModelVersionSerializer,
    TrainingSampleSerializer,
)
from .services import get_model_service_url


class TrainingSampleViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Training sample review queue."""

    serializer_class = TrainingSampleSerializer
    pagination_class = StandardResultsSetPagination
    queryset = TrainingSample.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        status_value = params.get("status")
        if status_value:
            if status_value not in TrainingSample.Status.values:
                raise ValidationError({"status": "Unsupported status."})
            queryset = queryset.filter(status=status_value)

        source = params.get("source")
        if source:
            queryset = queryset.filter(source=source)

        label = params.get("label") or params.get("mapped_label")
        if label:
            queryset = queryset.filter(mapped_label=label)

        raw_label = params.get("raw_label")
        if raw_label:
            queryset = queryset.filter(raw_label=raw_label)

        search = params.get("search") or params.get("q")
        if search:
            queryset = queryset.filter(text__icontains=search)

        return queryset

    @action(detail=True, methods=("post",))
    def correct(self, request, pk=None):
        serializer = CorrectTrainingSampleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sample = self.get_object()
        sample.corrected_label = serializer.validated_data["corrected_label"]
        sample.reviewer = serializer.validated_data.get("reviewer") or _request_reviewer(request)
        sample.status = TrainingSample.Status.REVIEWED
        sample.save(update_fields=("corrected_label", "reviewer", "status", "updated_at"))

        return Response(self.get_serializer(sample).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=("post",))
    def ignore(self, request, pk=None):
        serializer = IgnoreTrainingSampleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sample = self.get_object()
        sample.reviewer = serializer.validated_data.get("reviewer") or _request_reviewer(request)
        sample.status = TrainingSample.Status.IGNORED
        sample.save(update_fields=("reviewer", "status", "updated_at"))

        return Response(self.get_serializer(sample).data, status=status.HTTP_200_OK)


class ModelVersionViewSet(viewsets.ReadOnlyModelViewSet):
    """Registered model versions."""

    serializer_class = ModelVersionSerializer
    pagination_class = StandardResultsSetPagination
    queryset = ModelVersion.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        model_type = params.get("model_type")
        if model_type:
            queryset = queryset.filter(model_type=model_type)

        is_active = params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() in {"1", "true", "yes", "on"})

        return queryset

    @action(detail=True, methods=("post",))
    def activate(self, request, pk=None):
        with transaction.atomic():
            model_version = self.get_object()
            ModelVersion.objects.exclude(pk=model_version.pk).update(is_active=False)
            model_version.is_active = True
            model_version.save(update_fields=("is_active", "updated_at"))

        return Response(self.get_serializer(model_version).data, status=status.HTTP_200_OK)


class InferenceLogViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Inference log query endpoint."""

    serializer_class = InferenceLogSerializer
    pagination_class = StandardResultsSetPagination
    queryset = InferenceLog.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        label = params.get("label") or params.get("predicted_label")
        if label:
            queryset = queryset.filter(predicted_label=label)

        for field_name in ("model_version", "request_source", "text_hash"):
            value = params.get(field_name)
            if value:
                queryset = queryset.filter(**{field_name: value})

        return queryset


class ModelStatusView(APIView):
    """Current model state summary for the admin console."""

    def get(self, request):
        active_model = ModelVersion.objects.filter(is_active=True).first()
        latest_model = ModelVersion.objects.first()
        inference_stats = InferenceLog.objects.aggregate(
            total=Count("id"),
            last_created_at=Max("created_at"),
        )

        return Response(
            {
                "model_service_url": get_model_service_url(),
                "active_model": ModelVersionSerializer(active_model).data if active_model else None,
                "latest_model": ModelVersionSerializer(latest_model).data if latest_model else None,
                "inference": {
                    "total": inference_stats["total"],
                    "last_created_at": inference_stats["last_created_at"],
                },
            }
        )


def _request_reviewer(request) -> str:
    user = getattr(request, "user", None)
    if not user or getattr(user, "is_anonymous", False):
        return ""
    return str(getattr(user, "username", "") or getattr(user, "pk", "") or "")
