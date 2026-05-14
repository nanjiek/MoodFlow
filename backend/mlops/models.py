from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class TrainingSample(models.Model):
    """Training corpus item used by the emotion model workflow."""

    class Status(models.TextChoices):
        ACTIVE = "active", _("Active")
        REVIEWED = "reviewed", _("Reviewed")
        IGNORED = "ignored", _("Ignored")

    text = models.TextField("样本文本")
    raw_label = models.CharField("原始标签", max_length=64, blank=True, db_index=True)
    mapped_label = models.CharField("映射标签", max_length=64, db_index=True)
    source = models.CharField("样本来源", max_length=128, blank=True, db_index=True)
    status = models.CharField(
        "状态",
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    reviewer = models.CharField("审核人", max_length=150, blank=True)
    corrected_label = models.CharField("修正标签", max_length=64, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "mlops_training_sample"
        ordering = ("-created_at", "-id")
        indexes = (
            models.Index(fields=("status", "mapped_label"), name="mlops_ts_status_label_idx"),
            models.Index(fields=("source", "status"), name="mlops_ts_source_status_idx"),
        )
        verbose_name = "训练样本"
        verbose_name_plural = "训练样本"

    def __str__(self):
        return f"{self.mapped_label}:{self.text[:32]}"


class ModelVersion(models.Model):
    """Registered model artifact and metrics."""

    name = models.CharField("模型名称", max_length=128)
    version = models.CharField("版本号", max_length=64, unique=True, db_index=True)
    model_type = models.CharField("模型类型", max_length=64, db_index=True)
    artifact_path = models.CharField("产物路径", max_length=500)
    metrics = models.JSONField("指标", default=dict, blank=True)
    is_active = models.BooleanField("是否激活", default=False, db_index=True)
    trained_at = models.DateTimeField("训练时间", default=timezone.now, db_index=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "mlops_model_version"
        ordering = ("-trained_at", "-id")
        indexes = (
            models.Index(fields=("model_type", "is_active"), name="mlops_mv_type_active_idx"),
            models.Index(fields=("is_active", "-trained_at"), name="mlops_mv_active_trained_idx"),
        )
        verbose_name = "模型版本"
        verbose_name_plural = "模型版本"

    def __str__(self):
        return f"{self.name}:{self.version}"


class InferenceLog(models.Model):
    """Prediction request log captured from the backend model gateway."""

    text_hash = models.CharField("文本哈希", max_length=64, db_index=True)
    predicted_label = models.CharField("预测标签", max_length=64, db_index=True)
    confidence = models.FloatField(
        "置信度",
        default=0,
        validators=(MinValueValidator(0), MaxValueValidator(1)),
    )
    model_version = models.CharField("模型版本", max_length=64, blank=True, db_index=True)
    latency_ms = models.PositiveIntegerField("耗时毫秒", default=0)
    request_source = models.CharField("请求来源", max_length=64, default="model_service", db_index=True)
    raw_result = models.JSONField("原始结果", default=dict, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True, db_index=True)

    class Meta:
        db_table = "mlops_inference_log"
        ordering = ("-created_at", "-id")
        indexes = (
            models.Index(fields=("text_hash", "-created_at"), name="mlops_il_hash_created_idx"),
            models.Index(fields=("predicted_label", "-created_at"), name="mlops_il_label_created_idx"),
            models.Index(fields=("model_version", "-created_at"), name="mlops_il_version_created_idx"),
        )
        verbose_name = "推理日志"
        verbose_name_plural = "推理日志"

    def __str__(self):
        return f"{self.predicted_label}({self.confidence:.2f})@{self.created_at:%Y-%m-%d %H:%M:%S}"
