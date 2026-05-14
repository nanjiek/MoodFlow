from rest_framework import serializers

from .models import AdminOperationLog, FeatureUsageLog


class StatisticsQuerySerializer(serializers.Serializer):
    days = serializers.IntegerField(required=False, min_value=1, max_value=366, default=30)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    date_from = serializers.DateField(required=False, write_only=True)
    date_to = serializers.DateField(required=False, write_only=True)

    def validate(self, attrs):
        start_date = attrs.get("start_date") or attrs.pop("date_from", None)
        end_date = attrs.get("end_date") or attrs.pop("date_to", None)
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("start_date must be earlier than or equal to end_date.")
        attrs["start_date"] = start_date
        attrs["end_date"] = end_date
        return attrs


class FeatureUsageQuerySerializer(StatisticsQuerySerializer):
    feature = serializers.CharField(required=False, allow_blank=True, max_length=80)
    action = serializers.CharField(required=False, allow_blank=True, max_length=80)


class TimelineQuerySerializer(StatisticsQuerySerializer):
    date = serializers.DateField(required=False)
    refresh = serializers.BooleanField(required=False, default=False)


class OperationLogQuerySerializer(serializers.Serializer):
    admin_id = serializers.IntegerField(required=False)
    admin_username = serializers.CharField(required=False, allow_blank=True, max_length=150)
    action = serializers.CharField(required=False, allow_blank=True, max_length=100)
    target_type = serializers.CharField(required=False, allow_blank=True, max_length=100)
    target_id = serializers.CharField(required=False, allow_blank=True, max_length=100)
    ip_address = serializers.IPAddressField(required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    date_from = serializers.DateField(required=False, write_only=True)
    date_to = serializers.DateField(required=False, write_only=True)

    def validate(self, attrs):
        start_date = attrs.get("start_date") or attrs.pop("date_from", None)
        end_date = attrs.get("end_date") or attrs.pop("date_to", None)
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("start_date must be earlier than or equal to end_date.")
        attrs["start_date"] = start_date
        attrs["end_date"] = end_date
        return attrs


class AdminOperationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminOperationLog
        fields = (
            "id",
            "admin_id",
            "admin_username",
            "action",
            "target_type",
            "target_id",
            "ip_address",
            "metadata",
            "created_at",
        )
        read_only_fields = fields


class FeatureUsageLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureUsageLog
        fields = (
            "id",
            "feature",
            "user_id",
            "action",
            "metadata",
            "created_at",
        )
        read_only_fields = fields
