from django.contrib import admin

from .models import AdminOperationLog, FeatureUsageLog


@admin.register(FeatureUsageLog)
class FeatureUsageLogAdmin(admin.ModelAdmin):
    list_display = ("id", "feature", "user_id", "action", "created_at")
    list_filter = ("feature", "action", "created_at")
    search_fields = ("feature", "user_id", "action")
    readonly_fields = ("created_at",)


@admin.register(AdminOperationLog)
class AdminOperationLogAdmin(admin.ModelAdmin):
    list_display = ("id", "admin_id", "admin_username", "action", "target_type", "target_id", "ip_address", "created_at")
    list_filter = ("action", "target_type", "created_at")
    search_fields = ("admin_username", "action", "target_type", "target_id", "ip_address")
    readonly_fields = ("created_at",)
