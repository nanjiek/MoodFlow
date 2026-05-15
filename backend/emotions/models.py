from django.contrib.auth.hashers import check_password as django_check_password
from django.contrib.auth.hashers import make_password
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class AppUser(models.Model):
    """MoodFlow 普通用户资料，独立于 Django auth.User。"""

    GENDER_UNKNOWN = "unknown"
    GENDER_MALE = "male"
    GENDER_FEMALE = "female"
    GENDER_OTHER = "other"

    GENDER_CHOICES = (
        (GENDER_UNKNOWN, "未知"),
        (GENDER_MALE, "男"),
        (GENDER_FEMALE, "女"),
        (GENDER_OTHER, "其他"),
    )

    external_id = models.CharField("外部用户ID", max_length=64, unique=True, blank=True, null=True)
    nickname = models.CharField("昵称", max_length=64)
    avatar_url = models.URLField("头像地址", max_length=500, blank=True)
    gender = models.CharField("性别", max_length=16, choices=GENDER_CHOICES, default=GENDER_UNKNOWN)
    birth_date = models.DateField("生日", blank=True, null=True)
    phone = models.CharField("手机号", max_length=32, blank=True)
    email = models.EmailField("邮箱", blank=True)
    password_hash = models.CharField("密码哈希", max_length=128, blank=True)
    signature = models.CharField("个性签名", max_length=255, blank=True)
    anonymous_mode = models.BooleanField("是否匿名模式", default=False)
    emotion_encryption_enabled = models.BooleanField("情绪加密开关", default=False)
    is_active = models.BooleanField("是否启用", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "emotions_app_user"
        ordering = ("-created_at",)
        verbose_name = "MoodFlow用户"
        verbose_name_plural = "MoodFlow用户"

    def __str__(self):
        return self.nickname

    @property
    def is_authenticated(self):
        return True

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        if not self.password_hash:
            return False
        return django_check_password(raw_password, self.password_hash)


class EmotionTag(models.Model):
    """MoodFlow 情绪标签。"""

    HAPPY = "happy"
    CALM = "calm"
    EXPECTING = "expecting"
    ANXIOUS = "anxious"
    SAD = "sad"
    IRRITABLE = "irritable"
    PLAIN = "plain"
    TIRED = "tired"

    MOODFLOW_CHOICES = (
        (HAPPY, "开心"),
        (CALM, "平静"),
        (EXPECTING, "期待"),
        (ANXIOUS, "焦虑"),
        (SAD, "难过"),
        (IRRITABLE, "烦躁"),
        (PLAIN, "平淡"),
        (TIRED, "疲惫"),
    )

    code = models.CharField("标签编码", max_length=32, unique=True, db_index=True)
    name = models.CharField("中文名", max_length=32)
    description = models.CharField("描述", max_length=255, blank=True)
    is_active = models.BooleanField("是否启用", default=True, db_index=True)
    sort_order = models.PositiveSmallIntegerField("排序", default=0)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "emotions_emotion_tag"
        ordering = ("sort_order", "id")
        verbose_name = "情绪标签"
        verbose_name_plural = "情绪标签"

    def __str__(self):
        return f"{self.name}({self.code})"


class EmotionRecord(models.Model):
    """用户情绪记录。"""

    SOURCE_MANUAL = "manual"
    SOURCE_IMPORT = "import"
    SOURCE_SYSTEM = "system"

    SOURCE_CHOICES = (
        (SOURCE_MANUAL, "手动记录"),
        (SOURCE_IMPORT, "导入"),
        (SOURCE_SYSTEM, "系统生成"),
    )

    user = models.ForeignKey(AppUser, related_name="emotion_records", on_delete=models.CASCADE, verbose_name="用户")
    emotion_text = models.TextField("情绪文本")
    tag = models.ForeignKey(EmotionTag, related_name="emotion_records", on_delete=models.PROTECT, verbose_name="情绪标签")
    emoji_id = models.CharField("表情ID", max_length=64, blank=True)
    recorded_at = models.DateTimeField("记录时间", default=timezone.now, db_index=True)
    is_collect = models.BooleanField("是否收藏", default=False)
    is_encrypted = models.BooleanField("是否加密", default=False)
    source = models.CharField("来源", max_length=32, choices=SOURCE_CHOICES, default=SOURCE_MANUAL, db_index=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "emotions_emotion_record"
        ordering = ("-recorded_at", "-id")
        indexes = (
            models.Index(fields=("user", "recorded_at"), name="idx_record_user_time"),
            models.Index(fields=("tag", "recorded_at"), name="idx_record_tag_time"),
        )
        verbose_name = "情绪记录"
        verbose_name_plural = "情绪记录"

    def __str__(self):
        return f"{self.user_id}:{self.tag.code}@{self.recorded_at:%Y-%m-%d %H:%M}"


class EmotionAnalysis(models.Model):
    """情绪分析结果。"""

    TREND_RISING = "rising"
    TREND_STABLE = "stable"
    TREND_FALLING = "falling"
    TREND_UNKNOWN = "unknown"

    TREND_CHOICES = (
        (TREND_RISING, "上升"),
        (TREND_STABLE, "稳定"),
        (TREND_FALLING, "下降"),
        (TREND_UNKNOWN, "未知"),
    )

    record = models.OneToOneField(EmotionRecord, related_name="analysis", on_delete=models.CASCADE, verbose_name="情绪记录")
    predicted_label = models.CharField("预测标签", max_length=32, db_index=True)
    confidence = models.FloatField("置信度", default=0, validators=(MinValueValidator(0), MaxValueValidator(1)))
    keywords = models.JSONField("关键词", default=list, blank=True)
    intensity = models.PositiveSmallIntegerField("强度", default=0, validators=(MinValueValidator(0), MaxValueValidator(10)))
    trend = models.CharField("趋势", max_length=32, choices=TREND_CHOICES, default=TREND_UNKNOWN)
    cause = models.TextField("原因", blank=True)
    model_version = models.CharField("模型版本", max_length=64, blank=True)
    raw_result = models.JSONField("原始结果", default=dict, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "emotions_emotion_analysis"
        ordering = ("-created_at",)
        verbose_name = "情绪分析"
        verbose_name_plural = "情绪分析"

    def __str__(self):
        return f"{self.record_id}:{self.predicted_label}({self.confidence:.2f})"


class UserReminderPreference(models.Model):
    user = models.OneToOneField(AppUser, related_name="reminder_preference", on_delete=models.CASCADE)
    enabled = models.BooleanField(default=True)
    timezone = models.CharField(max_length=64, default="Asia/Shanghai")
    reminder_time = models.TimeField(default="09:00")
    quiet_hours_start = models.TimeField(default="22:00")
    quiet_hours_end = models.TimeField(default="08:00")
    frequency_per_day = models.PositiveSmallIntegerField(default=1)
    preferred_content_types = models.JSONField(default=list, blank=True)
    last_triggered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "emotions_user_reminder_preference"
        ordering = ("user_id",)

    def __str__(self):
        return f"reminder:{self.user_id}"


class UserDeviceToken(models.Model):
    class Platform(models.TextChoices):
        IOS = "ios", "iOS"
        ANDROID = "android", "Android"
        WEB = "web", "Web"

    user = models.ForeignKey(AppUser, related_name="device_tokens", on_delete=models.CASCADE)
    token = models.CharField(max_length=512, unique=True)
    platform = models.CharField(max_length=16, choices=Platform.choices, default=Platform.ANDROID)
    device_id = models.CharField(max_length=128, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    last_seen_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "emotions_user_device_token"
        ordering = ("-updated_at", "-id")
        indexes = (
            models.Index(fields=("user", "is_active"), name="emo_dev_user_active_idx"),
            models.Index(fields=("platform", "is_active"), name="emo_dev_platform_idx"),
        )

    def __str__(self):
        return f"{self.user_id}:{self.platform}:{self.device_id or self.id}"


class ReminderDispatchLog(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"
        RETRYING = "retrying", "Retrying"

    user = models.ForeignKey(AppUser, related_name="reminder_dispatch_logs", on_delete=models.CASCADE)
    device = models.ForeignKey(UserDeviceToken, related_name="dispatch_logs", null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    response_payload = models.JSONField(default=dict, blank=True)
    attempt_count = models.PositiveSmallIntegerField(default=0)
    last_error = models.TextField(blank=True)
    next_retry_at = models.DateTimeField(null=True, blank=True, db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "emotions_reminder_dispatch_log"
        ordering = ("-created_at", "-id")
        indexes = (
            models.Index(fields=("user", "status"), name="emo_rem_user_status_idx"),
            models.Index(fields=("status", "next_retry_at"), name="emo_rem_retry_idx"),
        )

    def __str__(self):
        return f"reminder:{self.user_id}:{self.status}"


class EmotionDataExportTask(models.Model):
    class Format(models.TextChoices):
        JSON = "json", "JSON"
        CSV = "csv", "CSV"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(AppUser, related_name="export_tasks", on_delete=models.CASCADE)
    file_format = models.CharField(max_length=16, choices=Format.choices, db_index=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    record_count = models.PositiveIntegerField(default=0)
    file_name = models.CharField(max_length=255, blank=True)
    content = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "emotions_data_export_task"
        ordering = ("-created_at", "-id")
        indexes = (
            models.Index(fields=("user", "status"), name="emo_exp_user_status_idx"),
            models.Index(fields=("file_format", "created_at"), name="emo_exp_format_time_idx"),
        )

    def __str__(self):
        return f"export:{self.user_id}:{self.file_format}:{self.status}"
