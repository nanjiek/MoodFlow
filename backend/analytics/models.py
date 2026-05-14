from django.db import models


class FeatureUsageLog(models.Model):
    feature = models.CharField(max_length=80, db_index=True)
    user_id = models.CharField(max_length=64, blank=True, db_index=True)
    action = models.CharField(max_length=80, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "analytics_feature_usage_log"
        ordering = ("-created_at", "-id")
        indexes = (
            models.Index(fields=("feature", "created_at"), name="analytics_ful_feature_time_idx"),
            models.Index(fields=("user_id", "created_at"), name="analytics_ful_user_time_idx"),
            models.Index(fields=("action", "created_at"), name="analytics_ful_action_time_idx"),
        )

    def __str__(self):
        return f"{self.feature}:{self.action}@{self.created_at:%Y-%m-%d %H:%M:%S}"


class AdminOperationLog(models.Model):
    admin_id = models.PositiveBigIntegerField(null=True, blank=True, db_index=True)
    admin_username = models.CharField(max_length=150, blank=True, db_index=True)
    action = models.CharField(max_length=100, db_index=True)
    target_type = models.CharField(max_length=100, blank=True, db_index=True)
    target_id = models.CharField(max_length=100, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "analytics_admin_operation_log"
        ordering = ("-created_at", "-id")
        indexes = (
            models.Index(fields=("admin_id", "created_at"), name="analytics_aol_admin_time_idx"),
            models.Index(fields=("action", "created_at"), name="analytics_aol_action_time_idx"),
            models.Index(fields=("target_type", "target_id"), name="analytics_aol_target_idx"),
        )

    def __str__(self):
        actor = self.admin_username or self.admin_id or "anonymous"
        return f"{actor}:{self.action}@{self.created_at:%Y-%m-%d %H:%M:%S}"

    def save(self, *args, **kwargs):
        if not self.admin_username and isinstance(self.metadata, dict):
            username = self.metadata.get("username") or self.metadata.get("operator")
            if username:
                self.admin_username = str(username)[:150]
        super().save(*args, **kwargs)
