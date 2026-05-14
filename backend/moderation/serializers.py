from rest_framework import serializers

from .models import TreeHoleComment, TreeHolePost


class TreeHoleCommentSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = TreeHoleComment
        fields = [
            "id",
            "post",
            "user_id",
            "anonymous_id",
            "content",
            "created_at",
        ]
        read_only_fields = fields


class TreeHolePostListSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    emotion_tag_id = serializers.IntegerField(read_only=True)
    emotion_tag_name = serializers.StringRelatedField(source="emotion_tag", read_only=True)
    reviewed_by_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = TreeHolePost
        fields = [
            "id",
            "user_id",
            "anonymous_id",
            "content",
            "emotion_tag_id",
            "emotion_tag_name",
            "status",
            "reject_reason",
            "reviewed_by_id",
            "reviewed_at",
            "created_at",
        ]
        read_only_fields = fields


class TreeHolePostDetailSerializer(TreeHolePostListSerializer):
    comments = TreeHoleCommentSerializer(many=True, read_only=True)

    class Meta(TreeHolePostListSerializer.Meta):
        fields = TreeHolePostListSerializer.Meta.fields + ["comments"]
        read_only_fields = fields


class RejectTreeHolePostSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500, trim_whitespace=True)
