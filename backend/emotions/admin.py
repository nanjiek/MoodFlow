from django.contrib import admin

from .models import AppUser, EmotionAnalysis, EmotionRecord, EmotionTag


@admin.register(AppUser)
class AppUserAdmin(admin.ModelAdmin):
    list_display = ("id", "nickname", "external_id", "gender", "is_active", "created_at")
    list_filter = ("gender", "is_active")
    search_fields = ("nickname", "external_id", "phone", "email")
    ordering = ("-created_at",)


@admin.register(EmotionTag)
class EmotionTagAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name", "is_active", "sort_order", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("code", "name")
    ordering = ("sort_order", "id")


@admin.register(EmotionRecord)
class EmotionRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "tag", "source", "is_collect", "is_encrypted", "recorded_at")
    list_filter = ("tag", "source", "is_collect", "is_encrypted")
    search_fields = ("user__nickname", "emotion_text", "emoji_id")
    date_hierarchy = "recorded_at"
    ordering = ("-recorded_at",)


@admin.register(EmotionAnalysis)
class EmotionAnalysisAdmin(admin.ModelAdmin):
    list_display = ("id", "record", "predicted_label", "confidence", "intensity", "trend", "model_version")
    list_filter = ("predicted_label", "trend", "model_version")
    search_fields = ("record__emotion_text", "cause", "model_version")
    ordering = ("-created_at",)
