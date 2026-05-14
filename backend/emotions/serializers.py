from rest_framework import serializers

from .models import AppUser, EmotionAnalysis, EmotionRecord, EmotionTag


class AppUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppUser
        fields = (
            "id",
            "external_id",
            "nickname",
            "avatar_url",
            "gender",
            "birth_date",
            "phone",
            "email",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class AppUserBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppUser
        fields = ("id", "external_id", "nickname", "avatar_url")


class EmotionTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmotionTag
        fields = (
            "id",
            "code",
            "name",
            "description",
            "is_active",
            "sort_order",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class EmotionAnalysisSerializer(serializers.ModelSerializer):
    record_id = serializers.IntegerField(source="record.id", read_only=True)
    user_id = serializers.IntegerField(source="record.user_id", read_only=True)
    tag = EmotionTagSerializer(source="record.tag", read_only=True)

    class Meta:
        model = EmotionAnalysis
        fields = (
            "id",
            "record",
            "record_id",
            "user_id",
            "tag",
            "predicted_label",
            "confidence",
            "keywords",
            "intensity",
            "trend",
            "cause",
            "model_version",
            "raw_result",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class EmotionRecordSerializer(serializers.ModelSerializer):
    user_detail = AppUserBriefSerializer(source="user", read_only=True)
    tag_detail = EmotionTagSerializer(source="tag", read_only=True)
    analysis = EmotionAnalysisSerializer(read_only=True)

    class Meta:
        model = EmotionRecord
        fields = (
            "id",
            "user",
            "user_detail",
            "emotion_text",
            "tag",
            "tag_detail",
            "emoji_id",
            "recorded_at",
            "is_collect",
            "is_encrypted",
            "source",
            "analysis",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")
