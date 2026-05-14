from django.contrib import admin

from .models import CompanionContent, SystemConfig


@admin.register(CompanionContent)
class CompanionContentAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "content_type", "emotion_tag", "weight", "is_active", "updated_at")
    list_filter = ("content_type", "is_active", "emotion_tag")
    search_fields = ("title", "body", "resource_url")
    ordering = ("-weight", "id")


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ("key", "is_public", "updated_at")
    list_filter = ("is_public",)
    search_fields = ("key", "description")
