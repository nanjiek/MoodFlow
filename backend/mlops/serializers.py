from rest_framework import serializers

from .models import InferenceLog, ModelVersion, TrainingSample


class TrainingSampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingSample
        fields = (
            "id",
            "text",
            "raw_label",
            "mapped_label",
            "source",
            "status",
            "reviewer",
            "corrected_label",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class CorrectTrainingSampleSerializer(serializers.Serializer):
    corrected_label = serializers.CharField(max_length=64, trim_whitespace=True)
    reviewer = serializers.CharField(max_length=150, required=False, allow_blank=True, trim_whitespace=True)


class IgnoreTrainingSampleSerializer(serializers.Serializer):
    reviewer = serializers.CharField(max_length=150, required=False, allow_blank=True, trim_whitespace=True)


class ModelVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelVersion
        fields = (
            "id",
            "name",
            "version",
            "model_type",
            "artifact_path",
            "metrics",
            "is_active",
            "trained_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class InferenceLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = InferenceLog
        fields = (
            "id",
            "text_hash",
            "predicted_label",
            "confidence",
            "model_version",
            "latency_ms",
            "request_source",
            "raw_result",
            "created_at",
        )
        read_only_fields = fields
