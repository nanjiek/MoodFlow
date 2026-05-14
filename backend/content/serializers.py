from django.apps import apps
from rest_framework import serializers

from .models import CompanionContent, SystemConfig


def get_emotion_tag_model():
    return apps.get_model("emotions", "EmotionTag")


class EmotionTagPrimaryKeyField(serializers.PrimaryKeyRelatedField):
    def __init__(self, **kwargs):
        kwargs.setdefault("queryset", get_emotion_tag_model().objects.all())
        super().__init__(**kwargs)

    def get_queryset(self):
        return get_emotion_tag_model().objects.all()


class CompanionContentSerializer(serializers.ModelSerializer):
    emotion_tag = EmotionTagPrimaryKeyField(allow_null=True, required=False)
    emotion_tag_detail = serializers.SerializerMethodField()

    class Meta:
        model = CompanionContent
        fields = (
            "id",
            "content_type",
            "emotion_tag",
            "emotion_tag_detail",
            "title",
            "body",
            "resource_url",
            "weight",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "emotion_tag_detail", "created_at", "updated_at")

    def get_emotion_tag_detail(self, obj):
        if not obj.emotion_tag_id:
            return None

        tag = obj.emotion_tag
        detail = {"id": tag.pk}
        for attr in ("code", "name", "label", "slug"):
            if hasattr(tag, attr):
                detail[attr] = getattr(tag, attr)
        return detail


class SystemConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemConfig
        fields = (
            "id",
            "key",
            "value",
            "description",
            "is_public",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "key", "created_at", "updated_at")
