from django.db import models


class CompanionContent(models.Model):
    CONTENT_TYPE_PHRASE = "phrase"
    CONTENT_TYPE_ADVICE = "advice"
    CONTENT_TYPE_MUSIC = "music"
    CONTENT_TYPE_ARTICLE = "article"
    CONTENT_TYPE_BREATHING = "breathing"
    CONTENT_TYPE_TEMPLATE = "template"

    CONTENT_TYPE_CHOICES = (
        (CONTENT_TYPE_PHRASE, "Phrase"),
        (CONTENT_TYPE_ADVICE, "Advice"),
        (CONTENT_TYPE_MUSIC, "Music"),
        (CONTENT_TYPE_ARTICLE, "Article"),
        (CONTENT_TYPE_BREATHING, "Breathing"),
        (CONTENT_TYPE_TEMPLATE, "Template"),
    )

    emotion_tag = models.ForeignKey(
        "emotions.EmotionTag",
        related_name="companion_contents",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    title = models.CharField(max_length=120)
    body = models.TextField(blank=True)
    resource_url = models.URLField(max_length=500, blank=True)
    weight = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-weight", "id")
        indexes = (
            models.Index(fields=("content_type", "is_active")),
            models.Index(fields=("is_active", "weight")),
            models.Index(fields=("emotion_tag", "is_active")),
        )

    def __str__(self):
        return f"{self.get_content_type_display()}: {self.title}"


class SystemConfig(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.JSONField(default=dict)
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("key",)
        indexes = (
            models.Index(fields=("key", "is_public")),
        )

    def __str__(self):
        return self.key
