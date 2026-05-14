from datetime import datetime, time

from django.db.models import Q
from django.http import Http404
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from common.pagination import StandardResultsSetPagination

from .models import AppUser, EmotionAnalysis, EmotionRecord, EmotionTag
from .serializers import AppUserSerializer, EmotionAnalysisSerializer, EmotionRecordSerializer, EmotionTagSerializer


def _parse_datetime_bound(value, end_of_day=False):
    if not value:
        return None

    parsed = parse_datetime(value)
    if parsed is None:
        parsed_date = parse_date(value)
        if parsed_date is None:
            return None
        parsed = datetime.combine(parsed_date, time.max if end_of_day else time.min)

    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


class EmotionTagViewSet(viewsets.ModelViewSet):
    """后台情绪标签管理：分页查询、新增、编辑、启停。"""

    serializer_class = EmotionTagSerializer
    pagination_class = StandardResultsSetPagination
    queryset = EmotionTag.objects.all()
    http_method_names = ("get", "post", "put", "patch", "head", "options")

    def get_queryset(self):
        queryset = super().get_queryset()
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() in ("1", "true", "yes"))
        return queryset

    @action(detail=True, methods=("post",))
    def enable(self, request, pk=None):
        tag = self.get_object()
        tag.is_active = True
        tag.save(update_fields=("is_active", "updated_at"))
        return Response(self.get_serializer(tag).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=("post",))
    def disable(self, request, pk=None):
        tag = self.get_object()
        tag.is_active = False
        tag.save(update_fields=("is_active", "updated_at"))
        return Response(self.get_serializer(tag).data, status=status.HTTP_200_OK)


class AppUserViewSet(viewsets.ModelViewSet):
    """后台用户管理：列表、详情、资料编辑、启用/禁用。"""

    serializer_class = AppUserSerializer
    pagination_class = StandardResultsSetPagination
    queryset = AppUser.objects.all()
    http_method_names = ("get", "post", "put", "patch", "head", "options")

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        search = params.get("search") or params.get("q")
        if search:
            queryset = queryset.filter(Q(nickname__icontains=search) | Q(phone__icontains=search) | Q(email__icontains=search))

        external_id = params.get("external_id")
        if external_id:
            queryset = queryset.filter(external_id=external_id)

        is_active = params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() in ("1", "true", "yes", "on"))

        date_from = _parse_datetime_bound(params.get("date_from"))
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)

        date_to = _parse_datetime_bound(params.get("date_to"), end_of_day=True)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)

        return queryset

    @action(detail=True, methods=("post",))
    def enable(self, request, pk=None):
        user = self.get_object()
        user.is_active = True
        user.save(update_fields=("is_active", "updated_at"))
        return Response(self.get_serializer(user).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=("post",))
    def disable(self, request, pk=None):
        user = self.get_object()
        user.is_active = False
        user.save(update_fields=("is_active", "updated_at"))
        return Response(self.get_serializer(user).data, status=status.HTTP_200_OK)


class EmotionRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """后台用户情绪记录查询。"""

    serializer_class = EmotionRecordSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = EmotionRecord.objects.select_related("user", "tag", "analysis").all()
        params = self.request.query_params

        user_id = params.get("user_id")
        if user_id:
            if not user_id.isdigit():
                return queryset.none()
            queryset = queryset.filter(user_id=user_id)

        tag = params.get("tag")
        if tag:
            tag_filter = Q(tag__code=tag)
            if tag.isdigit():
                tag_filter |= Q(tag_id=tag)
            queryset = queryset.filter(tag_filter)

        date_from = _parse_datetime_bound(params.get("date_from"))
        if date_from:
            queryset = queryset.filter(recorded_at__gte=date_from)

        date_to = _parse_datetime_bound(params.get("date_to"), end_of_day=True)
        if date_to:
            queryset = queryset.filter(recorded_at__lte=date_to)

        return queryset


class EmotionAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    """后台情绪分析详情查询。"""

    serializer_class = EmotionAnalysisSerializer
    pagination_class = StandardResultsSetPagination
    queryset = EmotionAnalysis.objects.select_related("record", "record__user", "record__tag").all()


class EmotionAnalysisByRecordView(APIView):
    def get(self, request, record_pk):
        try:
            analysis = EmotionAnalysis.objects.select_related("record", "record__user", "record__tag").get(record_id=record_pk)
        except EmotionAnalysis.DoesNotExist as exc:
            raise Http404("Emotion analysis does not exist for this record.") from exc

        serializer = EmotionAnalysisSerializer(analysis)
        return Response(serializer.data)
