from django.contrib import admin

from .models import InferenceLog, ModelVersion, TrainingSample


@admin.register(TrainingSample)
class TrainingSampleAdmin(admin.ModelAdmin):
    list_display = ("id", "mapped_label", "raw_label", "source", "status", "reviewer", "updated_at")
    list_filter = ("status", "mapped_label", "source")
    search_fields = ("text", "raw_label", "mapped_label", "corrected_label", "reviewer")
    readonly_fields = ("created_at", "updated_at")


@admin.register(ModelVersion)
class ModelVersionAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "version", "model_type", "is_active", "trained_at")
    list_filter = ("model_type", "is_active")
    search_fields = ("name", "version", "artifact_path")
    readonly_fields = ("created_at", "updated_at")


@admin.register(InferenceLog)
class InferenceLogAdmin(admin.ModelAdmin):
    list_display = ("id", "predicted_label", "confidence", "model_version", "request_source", "latency_ms", "created_at")
    list_filter = ("predicted_label", "model_version", "request_source")
    search_fields = ("text_hash", "model_version")
    readonly_fields = ("created_at",)
