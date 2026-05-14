# Generated manually for the mlops app initial schema.

import django.core.validators
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="InferenceLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("text_hash", models.CharField(db_index=True, max_length=64, verbose_name="文本哈希")),
                ("predicted_label", models.CharField(db_index=True, max_length=64, verbose_name="预测标签")),
                (
                    "confidence",
                    models.FloatField(
                        default=0,
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(1),
                        ],
                        verbose_name="置信度",
                    ),
                ),
                ("model_version", models.CharField(blank=True, db_index=True, max_length=64, verbose_name="模型版本")),
                ("latency_ms", models.PositiveIntegerField(default=0, verbose_name="耗时毫秒")),
                ("request_source", models.CharField(db_index=True, default="model_service", max_length=64, verbose_name="请求来源")),
                ("raw_result", models.JSONField(blank=True, default=dict, verbose_name="原始结果")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="创建时间")),
            ],
            options={
                "verbose_name": "推理日志",
                "verbose_name_plural": "推理日志",
                "db_table": "mlops_inference_log",
                "ordering": ("-created_at", "-id"),
            },
        ),
        migrations.CreateModel(
            name="ModelVersion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=128, verbose_name="模型名称")),
                ("version", models.CharField(db_index=True, max_length=64, unique=True, verbose_name="版本号")),
                ("model_type", models.CharField(db_index=True, max_length=64, verbose_name="模型类型")),
                ("artifact_path", models.CharField(max_length=500, verbose_name="产物路径")),
                ("metrics", models.JSONField(blank=True, default=dict, verbose_name="指标")),
                ("is_active", models.BooleanField(db_index=True, default=False, verbose_name="是否激活")),
                ("trained_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name="训练时间")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
            ],
            options={
                "verbose_name": "模型版本",
                "verbose_name_plural": "模型版本",
                "db_table": "mlops_model_version",
                "ordering": ("-trained_at", "-id"),
            },
        ),
        migrations.CreateModel(
            name="TrainingSample",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("text", models.TextField(verbose_name="样本文本")),
                ("raw_label", models.CharField(blank=True, db_index=True, max_length=64, verbose_name="原始标签")),
                ("mapped_label", models.CharField(db_index=True, max_length=64, verbose_name="映射标签")),
                ("source", models.CharField(blank=True, db_index=True, max_length=128, verbose_name="样本来源")),
                (
                    "status",
                    models.CharField(
                        choices=[("active", "Active"), ("reviewed", "Reviewed"), ("ignored", "Ignored")],
                        db_index=True,
                        default="active",
                        max_length=16,
                        verbose_name="状态",
                    ),
                ),
                ("reviewer", models.CharField(blank=True, max_length=150, verbose_name="审核人")),
                ("corrected_label", models.CharField(blank=True, max_length=64, verbose_name="修正标签")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
            ],
            options={
                "verbose_name": "训练样本",
                "verbose_name_plural": "训练样本",
                "db_table": "mlops_training_sample",
                "ordering": ("-created_at", "-id"),
            },
        ),
        migrations.AddIndex(
            model_name="inferencelog",
            index=models.Index(fields=["text_hash", "-created_at"], name="mlops_il_hash_created_idx"),
        ),
        migrations.AddIndex(
            model_name="inferencelog",
            index=models.Index(fields=["predicted_label", "-created_at"], name="mlops_il_label_created_idx"),
        ),
        migrations.AddIndex(
            model_name="inferencelog",
            index=models.Index(fields=["model_version", "-created_at"], name="mlops_il_version_created_idx"),
        ),
        migrations.AddIndex(
            model_name="modelversion",
            index=models.Index(fields=["model_type", "is_active"], name="mlops_mv_type_active_idx"),
        ),
        migrations.AddIndex(
            model_name="modelversion",
            index=models.Index(fields=["is_active", "-trained_at"], name="mlops_mv_active_trained_idx"),
        ),
        migrations.AddIndex(
            model_name="trainingsample",
            index=models.Index(fields=["status", "mapped_label"], name="mlops_ts_status_label_idx"),
        ),
        migrations.AddIndex(
            model_name="trainingsample",
            index=models.Index(fields=["source", "status"], name="mlops_ts_source_status_idx"),
        ),
    ]
