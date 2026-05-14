from rest_framework import serializers

from content.services import recommend_contents

from .models import AppUser, EmotionAnalysis, EmotionRecord, EmotionTag
from .presentation import build_analysis_explanation, build_gentle_feedback, emotion_presentation


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
            "signature",
            "anonymous_mode",
            "emotion_encryption_enabled",
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
    presentation = serializers.SerializerMethodField()

    class Meta:
        model = EmotionTag
        fields = (
            "id",
            "code",
            "name",
            "description",
            "presentation",
            "is_active",
            "sort_order",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def get_presentation(self, obj):
        return emotion_presentation(obj.code)


class EmotionAnalysisSerializer(serializers.ModelSerializer):
    record_id = serializers.IntegerField(source="record.id", read_only=True)
    user_id = serializers.IntegerField(source="record.user_id", read_only=True)
    tag = EmotionTagSerializer(source="record.tag", read_only=True)
    selected_label = serializers.CharField(source="record.tag.code", read_only=True)
    predicted_label_detail = serializers.SerializerMethodField()
    explanation = serializers.SerializerMethodField()
    gentle_feedback = serializers.SerializerMethodField()
    companion_suggestions = serializers.SerializerMethodField()

    class Meta:
        model = EmotionAnalysis
        fields = (
            "id",
            "record",
            "record_id",
            "user_id",
            "tag",
            "selected_label",
            "predicted_label",
            "confidence",
            "keywords",
            "intensity",
            "trend",
            "cause",
            "predicted_label_detail",
            "explanation",
            "gentle_feedback",
            "companion_suggestions",
            "model_version",
            "raw_result",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def get_predicted_label_detail(self, obj):
        return emotion_presentation(obj.predicted_label)

    def get_explanation(self, obj):
        return build_analysis_explanation(obj.predicted_label, obj.keywords, obj.cause)

    def get_gentle_feedback(self, obj):
        return build_gentle_feedback(obj.predicted_label, obj.intensity)

    def get_companion_suggestions(self, obj):
        focus = emotion_presentation(obj.predicted_label).get("companion_focus", [])
        items = recommend_contents(obj.predicted_label, limit=3, preferred_types=focus)
        return [
            {
                "id": item.id,
                "content_type": item.content_type,
                "title": item.title,
                "body": item.body,
                "resource_url": item.resource_url,
            }
            for item in items
        ]


class EmotionRecordSerializer(serializers.ModelSerializer):
    user_detail = AppUserBriefSerializer(source="user", read_only=True)
    tag_detail = EmotionTagSerializer(source="tag", read_only=True)
    text = serializers.CharField(source="emotion_text", read_only=True)
    selected_label = serializers.CharField(source="tag.code", read_only=True)
    selected_label_detail = EmotionTagSerializer(source="tag", read_only=True)
    analysis = EmotionAnalysisSerializer(read_only=True)

    class Meta:
        model = EmotionRecord
        fields = (
            "id",
            "user",
            "user_detail",
            "emotion_text",
            "text",
            "tag",
            "tag_detail",
            "selected_label",
            "selected_label_detail",
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


class UserEmotionRecordWriteSerializer(serializers.ModelSerializer):
    text = serializers.CharField(source="emotion_text", required=False, allow_blank=True, allow_null=True)
    selected_label = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = EmotionRecord
        fields = (
            "text",
            "selected_label",
            "emoji_id",
            "is_collect",
            "is_encrypted",
            "recorded_at",
        )

    def validate(self, attrs):
        attrs["emotion_text"] = attrs.get("emotion_text") or ""
        request = self.context.get("request")
        if self.instance is not None:
            attrs["user"] = self.instance.user
        elif request is None or not isinstance(getattr(request, "user", None), AppUser):
            raise serializers.ValidationError({"user": "Authenticated app user is required."})
        else:
            attrs["user"] = request.user

        selected_label = attrs.pop("selected_label", None)
        if selected_label is None and self.instance is not None:
            attrs["tag"] = self.instance.tag
            return attrs
        if selected_label is None:
            raise serializers.ValidationError({"selected_label": "This field is required."})
        selected_label = str(selected_label).strip()
        tag_queryset = EmotionTag.objects.filter(is_active=True)
        if selected_label.isdigit():
            tag = tag_queryset.filter(pk=int(selected_label)).first()
        else:
            tag = tag_queryset.filter(code=selected_label).first()
        if tag is None:
            raise serializers.ValidationError({"selected_label": "Unsupported emotion label."})
        attrs["tag"] = tag
        return attrs
