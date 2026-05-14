from datetime import datetime, time

from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView

from common.pagination import StandardResultsSetPagination
from common.response import APIResponse

from .models import AdminOperationLog
from .serializers import (
    AdminOperationLogSerializer,
    FeatureUsageQuerySerializer,
    OperationLogQuerySerializer,
    StatisticsQuerySerializer,
)
from . import services


class OverviewStatisticsView(APIView):
    def get(self, request):
        return APIResponse.success(data=services.overview())


class ActiveUsersStatisticsView(APIView):
    def get(self, request):
        params = _validated_query(StatisticsQuerySerializer, request)
        return APIResponse.success(data=_call_statistics(services.active_users, params))


class EmotionDistributionStatisticsView(APIView):
    def get(self, request):
        params = _validated_query(StatisticsQuerySerializer, request)
        return APIResponse.success(data=_call_statistics(services.emotion_distribution, params))


class FeatureUsageStatisticsView(APIView):
    def get(self, request):
        params = _validated_query(FeatureUsageQuerySerializer, request)
        return APIResponse.success(data=_call_statistics(services.feature_usage, params))


class AdminOperationLogListView(APIView):
    pagination_class = StandardResultsSetPagination

    def get(self, request):
        params = _validated_query(OperationLogQuerySerializer, request)
        queryset = _filter_operation_logs(AdminOperationLog.objects.all(), params)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = AdminOperationLogSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


def _validated_query(serializer_class, request):
    serializer = serializer_class(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


def _call_statistics(func, params):
    try:
        return func(**params)
    except ValueError as exc:
        raise ValidationError({"date": str(exc)}) from exc


def _filter_operation_logs(queryset, params):
    for field in ("admin_id", "action", "target_type", "target_id", "ip_address"):
        value = params.get(field)
        if value not in (None, ""):
            queryset = queryset.filter(**{field: value})

    admin_username = params.get("admin_username")
    if admin_username:
        queryset = queryset.filter(admin_username__icontains=admin_username)

    start_date = params.get("start_date")
    if start_date:
        queryset = queryset.filter(created_at__gte=_day_start(start_date))

    end_date = params.get("end_date")
    if end_date:
        queryset = queryset.filter(created_at__lte=_day_end(end_date))

    return queryset


def _day_start(day):
    return timezone.make_aware(datetime.combine(day, time.min), timezone.get_current_timezone())


def _day_end(day):
    return timezone.make_aware(datetime.combine(day, time.max), timezone.get_current_timezone())
