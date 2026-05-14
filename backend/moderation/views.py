from datetime import datetime, time

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import status as drf_status
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .audit import write_admin_operation_log
from .models import TreeHolePost
from .serializers import (
    RejectTreeHolePostSerializer,
    TreeHolePostDetailSerializer,
    TreeHolePostListSerializer,
)


class TreeHolePostPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class TreeHolePostListView(APIView):
    def get(self, request):
        queryset = TreeHolePost.objects.select_related(
            "user",
            "emotion_tag",
            "reviewed_by",
        ).order_by("-created_at")
        queryset = _filter_posts(queryset, request.query_params)

        paginator = TreeHolePostPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = TreeHolePostListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class TreeHolePostDetailView(APIView):
    def get(self, request, pk):
        post = _get_post(pk)
        serializer = TreeHolePostDetailSerializer(post)
        return Response(serializer.data)


class TreeHolePostApproveView(APIView):
    def post(self, request, pk):
        post = _get_post(pk)
        post.status = TreeHolePost.Status.APPROVED
        post.reject_reason = ""
        post.reviewed_by = _resolve_reviewer(request)
        post.reviewed_at = timezone.now()
        post.save(update_fields=["status", "reject_reason", "reviewed_by", "reviewed_at"])

        write_admin_operation_log(request, "tree_hole_post_approve", post)
        serializer = TreeHolePostDetailSerializer(post)
        return Response(serializer.data, status=drf_status.HTTP_200_OK)


class TreeHolePostRejectView(APIView):
    def post(self, request, pk):
        serializer = RejectTreeHolePostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        post = _get_post(pk)
        reason = serializer.validated_data["reason"]
        post.status = TreeHolePost.Status.REJECTED
        post.reject_reason = reason
        post.reviewed_by = _resolve_reviewer(request)
        post.reviewed_at = timezone.now()
        post.save(update_fields=["status", "reject_reason", "reviewed_by", "reviewed_at"])

        write_admin_operation_log(request, "tree_hole_post_reject", post, reason=reason)
        response_serializer = TreeHolePostDetailSerializer(post)
        return Response(response_serializer.data, status=drf_status.HTTP_200_OK)


def _get_post(pk):
    return get_object_or_404(
        TreeHolePost.objects.select_related("user", "emotion_tag", "reviewed_by").prefetch_related("comments"),
        pk=pk,
    )


def _filter_posts(queryset, params):
    status_value = params.get("status")
    if status_value:
        if status_value not in TreeHolePost.Status.values:
            raise ValidationError({"status": "Unsupported status."})
        queryset = queryset.filter(status=status_value)

    emotion_tag_id = params.get("emotion_tag") or params.get("emotion_tag_id")
    if emotion_tag_id:
        queryset = queryset.filter(emotion_tag_id=emotion_tag_id)

    created_after = params.get("created_after") or params.get("start_date") or params.get("date_from")
    if created_after:
        queryset = queryset.filter(
            created_at__gte=_parse_datetime_bound(created_after, "created_after"),
        )

    created_before = params.get("created_before") or params.get("end_date") or params.get("date_to")
    if created_before:
        queryset = queryset.filter(
            created_at__lte=_parse_datetime_bound(created_before, "created_before", end_of_day=True),
        )

    return queryset


def _parse_datetime_bound(value, param_name, end_of_day=False):
    parsed_datetime = parse_datetime(value)
    if parsed_datetime is None:
        parsed_date = parse_date(value)
        if parsed_date is None:
            raise ValidationError({param_name: "Use ISO datetime or YYYY-MM-DD."})
        parsed_time = time.max if end_of_day else time.min
        parsed_datetime = datetime.combine(parsed_date, parsed_time)

    if timezone.is_naive(parsed_datetime):
        parsed_datetime = timezone.make_aware(parsed_datetime, timezone.get_current_timezone())
    return parsed_datetime


def _resolve_reviewer(request):
    user = getattr(request, "user", None)
    if not user or getattr(user, "is_anonymous", False):
        return None

    reviewed_by_field = TreeHolePost._meta.get_field("reviewed_by")
    reviewer_model = reviewed_by_field.remote_field.model
    if isinstance(user, reviewer_model):
        return user

    user_id = getattr(user, "pk", None)
    if user_id is None:
        return None
    try:
        return reviewer_model.objects.filter(pk=user_id).first()
    except Exception:
        return None
