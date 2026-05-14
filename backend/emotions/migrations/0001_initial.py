import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AppUser",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("external_id", models.CharField(blank=True, max_length=64, null=True, unique=True, verbose_name="外部用户ID")),
                ("nickname", models.CharField(max_length=64, verbose_name="昵称")),
                ("avatar_url", models.URLField(blank=True, max_length=500, verbose_name="头像地址")),
                (
                    "gender",
                    models.CharField(
                        choices=[("unknown", "未知"), ("male", "男"), ("female", "女"), ("other", "其他")],
                        default="unknown",
                        max_length=16,
                        verbose_name="性别",
                    ),
                ),
                ("birth_date", models.DateField(blank=True, null=True, verbose_name="生日")),
                ("phone", models.CharField(blank=True, max_length=32, verbose_name="手机号")),
                ("email", models.EmailField(blank=True, max_length=254, verbose_name="邮箱")),
                ("is_active", models.BooleanField(default=True, verbose_name="是否启用")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
            ],
            options={
                "verbose_name": "MoodFlow用户",
                "verbose_name_plural": "MoodFlow用户",
                "db_table": "emotions_app_user",
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="EmotionTag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(db_index=True, max_length=32, unique=True, verbose_name="标签编码")),
                ("name", models.CharField(max_length=32, verbose_name="中文名")),
                ("description", models.CharField(blank=True, max_length=255, verbose_name="描述")),
                ("is_active", models.BooleanField(db_index=True, default=True, verbose_name="是否启用")),
                ("sort_order", models.PositiveSmallIntegerField(default=0, verbose_name="排序")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
            ],
            options={
                "verbose_name": "情绪标签",
                "verbose_name_plural": "情绪标签",
                "db_table": "emotions_emotion_tag",
                "ordering": ("sort_order", "id"),
            },
        ),
        migrations.CreateModel(
            name="EmotionRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("emotion_text", models.TextField(verbose_name="情绪文本")),
                ("emoji_id", models.CharField(blank=True, max_length=64, verbose_name="表情ID")),
                ("recorded_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name="记录时间")),
                ("is_collect", models.BooleanField(default=False, verbose_name="是否收藏")),
                ("is_encrypted", models.BooleanField(default=False, verbose_name="是否加密")),
                (
                    "source",
                    models.CharField(
                        choices=[("manual", "手动记录"), ("import", "导入"), ("system", "系统生成")],
                        db_index=True,
                        default="manual",
                        max_length=32,
                        verbose_name="来源",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                (
                    "tag",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="emotion_records",
                        to="emotions.emotiontag",
                        verbose_name="情绪标签",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="emotion_records",
                        to="emotions.appuser",
                        verbose_name="用户",
                    ),
                ),
            ],
            options={
                "verbose_name": "情绪记录",
                "verbose_name_plural": "情绪记录",
                "db_table": "emotions_emotion_record",
                "ordering": ("-recorded_at", "-id"),
                "indexes": [
                    models.Index(fields=["user", "recorded_at"], name="idx_record_user_time"),
                    models.Index(fields=["tag", "recorded_at"], name="idx_record_tag_time"),
                ],
            },
        ),
        migrations.CreateModel(
            name="EmotionAnalysis",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("predicted_label", models.CharField(db_index=True, max_length=32, verbose_name="预测标签")),
                (
                    "confidence",
                    models.FloatField(
                        default=0,
                        validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)],
                        verbose_name="置信度",
                    ),
                ),
                ("keywords", models.JSONField(blank=True, default=list, verbose_name="关键词")),
                (
                    "intensity",
                    models.PositiveSmallIntegerField(
                        default=0,
                        validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)],
                        verbose_name="强度",
                    ),
                ),
                (
                    "trend",
                    models.CharField(
                        choices=[("rising", "上升"), ("stable", "稳定"), ("falling", "下降"), ("unknown", "未知")],
                        default="unknown",
                        max_length=32,
                        verbose_name="趋势",
                    ),
                ),
                ("cause", models.TextField(blank=True, verbose_name="原因")),
                ("model_version", models.CharField(blank=True, max_length=64, verbose_name="模型版本")),
                ("raw_result", models.JSONField(blank=True, default=dict, verbose_name="原始结果")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                (
                    "record",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="analysis",
                        to="emotions.emotionrecord",
                        verbose_name="情绪记录",
                    ),
                ),
            ],
            options={
                "verbose_name": "情绪分析",
                "verbose_name_plural": "情绪分析",
                "db_table": "emotions_emotion_analysis",
                "ordering": ("-created_at",),
            },
        ),
    ]
