from collections import Counter
from datetime import datetime, time, timedelta

from django.db import transaction
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.http import Http404
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.authentication import UserJWTAuthentication
from accounts.permissions import IsAppUserAuthenticated
from analytics.serializers import TimelineQuerySerializer
from analytics.services import log_feature_usage, resolve_date_window, resolve_day_window
from common.pagination import StandardResultsSetPagination
from common.response import APIResponse
from mlops.services import call_model_service

from .exports import create_export_task
from .models import AppUser, EmotionAnalysis, EmotionDataExportTask, EmotionRecord, EmotionTag, UserDeviceToken
from .presentation import build_weekly_summary, emotion_growth_score, emotion_presentation, quick_entry_guide
from .reminders import get_or_create_reminder_preference, register_device_token, trigger_user_reminder
from .security import decrypt_text
from .serializers import (
    AppUserSerializer,
    EmotionExportCreateSerializer,
    EmotionExportTaskSerializer,
    EmotionAnalysisSerializer,
    EmotionRecordSerializer,
    EmotionTagSerializer,
    ReminderDispatchLogSerializer,
    UserDeviceTokenSerializer,
    UserEmotionRecordWriteSerializer,
    UserReminderPreferenceSerializer,
)


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


def _parse_bool_value(value):
    if isinstance(value, bool):
        return value
    if value in (None, ""):
        return None
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValidationError({"accepted": "Expected a boolean value."})


def _normalize_intensity(value):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = 0.0
    if parsed <= 1:
        parsed *= 10
    return min(max(int(round(parsed)), 0), 10)


def _resolve_trend(record, intensity):
    previous_analyses = list(
        EmotionAnalysis.objects.filter(
            record__user_id=record.user_id,
            record__recorded_at__lt=record.recorded_at,
        )
        .order_by("-record__recorded_at", "-id")
        .values_list("intensity", flat=True)[:5]
    )
    if not previous_analyses:
        return EmotionAnalysis.TREND_UNKNOWN

    baseline = sum(previous_analyses) / len(previous_analyses)
    if intensity >= baseline + 1:
        return EmotionAnalysis.TREND_RISING
    if intensity <= baseline - 1:
        return EmotionAnalysis.TREND_FALLING
    return EmotionAnalysis.TREND_STABLE


def _sync_record_analysis(record):
    plain_text = decrypt_text(record.emotion_text or "", is_encrypted=record.is_encrypted)
    prediction = call_model_service(plain_text, selected_label=record.tag.code)
    intensity = _normalize_intensity(prediction.get("intensity"))
    defaults = {
        "predicted_label": str(prediction.get("label") or record.tag.code),
        "confidence": min(max(float(prediction.get("confidence") or 0), 0.0), 1.0),
        "keywords": list(prediction.get("keywords") or []),
        "intensity": intensity,
        "trend": _resolve_trend(record, intensity),
        "cause": str(prediction.get("explanation") or ""),
        "model_version": str(prediction.get("model_version") or ""),
        "raw_result": prediction,
    }
    EmotionAnalysis.objects.update_or_create(record=record, defaults=defaults)


def _save_analysis_feedback(analysis, corrected_label, accepted, note):
    raw_result = dict(analysis.raw_result or {})
    raw_result["user_feedback"] = {
        "accepted": accepted if accepted is not None else False,
        "corrected_label": corrected_label or None,
        "note": note,
        "submitted_at": timezone.now().isoformat(),
    }
    analysis.raw_result = raw_result
    analysis.save(update_fields=("raw_result", "updated_at"))
    return raw_result["user_feedback"]


def _emotion_report_payload(queryset, start_at, end_at, request=None):
    records = list(queryset.select_related("tag", "analysis"))
    serialized_records = EmotionRecordSerializer(records, many=True, context={"request": request} if request else {}).data

    label_rows = []
    for record in records:
        try:
            analysis = record.analysis
        except EmotionAnalysis.DoesNotExist:
            analysis = None
        label = analysis.predicted_label if analysis and analysis.predicted_label else record.tag.code
        keywords = analysis.keywords if analysis else []
        label_rows.append({"label": label, "keywords": keywords or []})

    summary = build_weekly_summary(label_rows)
    counter = Counter(row["label"] for row in label_rows if row["label"])
    dominant_label = counter.most_common(1)[0][0] if counter else None
    dominant_emotion = emotion_presentation(dominant_label) if dominant_label else None
    breakdown = [
        {
            **emotion_presentation(label),
            "count": count,
            "ratio": round(count / len(label_rows), 4) if label_rows else 0,
        }
        for label, count in counter.most_common()
    ]

    days = (
        queryset.filter(recorded_at__gte=start_at, recorded_at__lte=end_at)
        .annotate(day=TruncDate("recorded_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )

    return {
        "start_at": start_at.isoformat(),
        "end_at": end_at.isoformat(),
        "total_records": len(records),
        "collect_count": sum(1 for record in records if record.is_collect),
        "dominant_emotion": dominant_emotion,
        "emotion_breakdown": breakdown,
        "summary": summary,
        "daily_series": list(days),
        "records": serialized_records,
    }


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

    @action(detail=False, methods=("get",), url_path="guide")
    def guide(self, request):
        return APIResponse.success(data=quick_entry_guide())

    @action(detail=False, methods=("get",), url_path="weekly-summary")
    def weekly_summary(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        limit = request.query_params.get("limit") or 7
        try:
            limit = min(max(int(limit), 1), 30)
        except (TypeError, ValueError):
            raise ValidationError({"limit": "Expected an integer between 1 and 30."})

        records = []
        for record in queryset[:limit]:
            keywords = []
            label = record.tag.code
            try:
                analysis = record.analysis
            except EmotionAnalysis.DoesNotExist:
                analysis = None
            if analysis:
                keywords = analysis.keywords or []
                label = analysis.predicted_label or label
            records.append(
                {
                    "label": label,
                    "keywords": keywords,
                }
            )

        return APIResponse.success(data=build_weekly_summary(records))


class EmotionAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    """后台情绪分析详情查询。"""

    serializer_class = EmotionAnalysisSerializer
    pagination_class = StandardResultsSetPagination
    queryset = EmotionAnalysis.objects.select_related("record", "record__user", "record__tag").all()

    @action(detail=True, methods=("post",))
    def correct(self, request, pk=None):
        analysis = self.get_object()
        corrected_label = (request.data.get("corrected_label") or "").strip()
        accepted = _parse_bool_value(request.data.get("accepted"))
        note = (request.data.get("note") or "").strip()

        if corrected_label and not EmotionTag.objects.filter(code=corrected_label).exists():
            raise ValidationError({"corrected_label": "Unsupported emotion label."})
        if accepted is None and not corrected_label:
            raise ValidationError({"accepted": "Provide accepted=false or a corrected_label."})
        feedback = _save_analysis_feedback(analysis, corrected_label, accepted, note)

        log_feature_usage(
            feature="emotion_analysis",
            action="correction_submitted",
            user_id=str(analysis.record.user_id),
            metadata={
                "record_id": analysis.record_id,
                "analysis_id": analysis.id,
                "predicted_label": analysis.predicted_label,
                "corrected_label": corrected_label,
                "accepted": feedback["accepted"],
            },
        )

        return APIResponse.success(
            data={
                "analysis_id": analysis.id,
                "predicted_label": analysis.predicted_label,
                "predicted_label_detail": emotion_presentation(analysis.predicted_label),
                "feedback_saved": True,
                "feedback": feedback,
            },
            message="feedback saved",
        )


class UserEmotionRecordViewSet(viewsets.ModelViewSet):
    serializer_class = EmotionRecordSerializer
    pagination_class = StandardResultsSetPagination
    authentication_classes = [UserJWTAuthentication]
    permission_classes = [IsAppUserAuthenticated]
    http_method_names = ("get", "post", "put", "patch", "delete", "head", "options")

    def get_queryset(self):
        queryset = EmotionRecord.objects.select_related("user", "tag", "analysis").filter(user=self.request.user)
        params = self.request.query_params

        selected_label = params.get("selected_label") or params.get("tag")
        if selected_label:
            tag_filter = Q(tag__code=selected_label)
            if selected_label.isdigit():
                tag_filter |= Q(tag_id=selected_label)
            queryset = queryset.filter(tag_filter)

        is_collect = _parse_bool_value(params.get("is_collect"))
        if is_collect is not None:
            queryset = queryset.filter(is_collect=is_collect)

        is_encrypted = _parse_bool_value(params.get("is_encrypted"))
        if is_encrypted is not None:
            queryset = queryset.filter(is_encrypted=is_encrypted)

        date_from = _parse_datetime_bound(params.get("date_from"))
        if date_from:
            queryset = queryset.filter(recorded_at__gte=date_from)

        date_to = _parse_datetime_bound(params.get("date_to"), end_of_day=True)
        if date_to:
            queryset = queryset.filter(recorded_at__lte=date_to)

        return queryset

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return UserEmotionRecordWriteSerializer
        return EmotionRecordSerializer

    def _get_owned_record(self):
        return self.get_object()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = EmotionRecordSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)
        serializer = EmotionRecordSerializer(queryset, many=True, context={"request": request})
        return APIResponse.success(data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        record = self._get_owned_record()
        serializer = self.get_serializer(record)
        return APIResponse.success(data=serializer.data)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        record = serializer.save()
        _sync_record_analysis(record)
        record.refresh_from_db()
        log_feature_usage("emotion_record", user_id=str(request.user.pk), action="create", metadata={"record_id": record.id})
        output = EmotionRecordSerializer(record, context={"request": request}).data
        return APIResponse.success(data=output, status_code=status.HTTP_201_CREATED, message="created")

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        record = self._get_owned_record()
        if "selected_label" not in request.data:
            raise ValidationError({"selected_label": "This field is required."})
        serializer = self.get_serializer(record, data=request.data, partial=partial, context={"request": request})
        serializer.is_valid(raise_exception=True)
        record = serializer.save()
        _sync_record_analysis(record)
        record.refresh_from_db()
        log_feature_usage("emotion_record", user_id=str(request.user.pk), action="update", metadata={"record_id": record.id})
        output = EmotionRecordSerializer(record, context={"request": request}).data
        return APIResponse.success(data=output, message="updated")

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        record = self._get_owned_record()
        log_feature_usage("emotion_record", user_id=str(request.user.pk), action="delete", metadata={"record_id": record.id})
        record.delete()
        return APIResponse.success(data={"id": record.id, "deleted": True}, message="deleted")

    @action(detail=True, methods=("post",), url_path="favorite")
    def favorite(self, request, pk=None):
        record = self._get_owned_record()
        explicit_value = _parse_bool_value(request.data.get("is_collect"))
        record.is_collect = (not record.is_collect) if explicit_value is None else explicit_value
        record.save(update_fields=("is_collect", "updated_at"))
        log_feature_usage("emotion_record", user_id=str(request.user.pk), action="favorite", metadata={"record_id": record.id, "is_collect": record.is_collect})
        return APIResponse.success(
            data={"id": record.id, "is_collect": record.is_collect},
            message="collect updated",
        )

    @action(detail=True, methods=("post",), url_path="toggle-collect")
    def toggle_collect(self, request, pk=None):
        return self.favorite(request, pk=pk)

    @action(detail=True, methods=("get",), url_path="analysis")
    def analysis(self, request, pk=None):
        record = self._get_owned_record()
        try:
            analysis = record.analysis
        except EmotionAnalysis.DoesNotExist as exc:
            raise Http404("Emotion analysis does not exist for this record.") from exc
        log_feature_usage("emotion_analysis", user_id=str(request.user.pk), action="view", metadata={"record_id": record.id, "analysis_id": analysis.id})
        return APIResponse.success(data=EmotionAnalysisSerializer(analysis).data)

    @action(detail=True, methods=("post",), url_path="analysis/correct")
    def analysis_correct(self, request, pk=None):
        record = self._get_owned_record()
        try:
            analysis = record.analysis
        except EmotionAnalysis.DoesNotExist as exc:
            raise Http404("Emotion analysis does not exist for this record.") from exc

        corrected_label = (request.data.get("corrected_label") or "").strip()
        accepted = _parse_bool_value(request.data.get("accepted"))
        note = (request.data.get("note") or "").strip()

        if corrected_label and not EmotionTag.objects.filter(code=corrected_label).exists():
            raise ValidationError({"corrected_label": "Unsupported emotion label."})
        if accepted is None and not corrected_label:
            raise ValidationError({"accepted": "Provide accepted=false or a corrected_label."})

        feedback = _save_analysis_feedback(analysis, corrected_label, accepted, note)
        log_feature_usage(
            feature="emotion_analysis",
            action="correction_submitted",
            user_id=str(record.user_id),
            metadata={
                "record_id": record.id,
                "analysis_id": analysis.id,
                "predicted_label": analysis.predicted_label,
                "corrected_label": corrected_label,
                "accepted": feedback["accepted"],
                "source": "user",
            },
        )
        return APIResponse.success(
            data={
                "analysis_id": analysis.id,
                "record_id": record.id,
                "feedback_saved": True,
                "feedback": feedback,
            },
            message="feedback saved",
        )

    @action(detail=False, methods=("get",), url_path="history-by-day")
    def history_by_day(self, request):
        raw_date = request.query_params.get("date")
        if not raw_date:
            raise ValidationError({"date": "date is required."})
        target_day = parse_date(raw_date)
        if target_day is None:
            raise ValidationError({"date": "Use YYYY-MM-DD."})
        start_at = timezone.make_aware(datetime.combine(target_day, time.min), timezone.get_current_timezone())
        end_at = timezone.make_aware(datetime.combine(target_day, time.max), timezone.get_current_timezone())
        queryset = self.get_queryset().filter(recorded_at__gte=start_at, recorded_at__lte=end_at)
        serializer = EmotionRecordSerializer(queryset, many=True, context={"request": request})
        log_feature_usage(
            feature="emotion_history_by_day",
            action="view",
            user_id=str(request.user.pk),
            metadata={"date": target_day.isoformat(), "record_count": queryset.count()},
        )
        return APIResponse.success(
            data={
                "date": target_day.isoformat(),
                "count": queryset.count(),
                "results": serializer.data,
            }
        )


class UserEmotionDailyReportView(APIView):
    authentication_classes = [UserJWTAuthentication]
    permission_classes = [IsAppUserAuthenticated]

    def get(self, request):
        report_date = parse_date(request.query_params.get("date") or "") or timezone.localdate()
        start_at = timezone.make_aware(datetime.combine(report_date, time.min), timezone.get_current_timezone())
        end_at = timezone.make_aware(datetime.combine(report_date, time.max), timezone.get_current_timezone())
        queryset = EmotionRecord.objects.filter(user=request.user, recorded_at__gte=start_at, recorded_at__lte=end_at)
        payload = _emotion_report_payload(queryset, start_at, end_at, request=request)
        payload["date"] = report_date.isoformat()
        return APIResponse.success(data=payload)


class UserEmotionWeeklyReportView(APIView):
    authentication_classes = [UserJWTAuthentication]
    permission_classes = [IsAppUserAuthenticated]

    def get(self, request):
        end_day = parse_date(request.query_params.get("end_date") or "") or timezone.localdate()
        start_day = parse_date(request.query_params.get("start_date") or "")
        if start_day is None:
            start_day = end_day - timedelta(days=6)
        if start_day > end_day:
            raise ValidationError({"start_date": "start_date must be earlier than or equal to end_date."})

        start_at = timezone.make_aware(datetime.combine(start_day, time.min), timezone.get_current_timezone())
        end_at = timezone.make_aware(datetime.combine(end_day, time.max), timezone.get_current_timezone())
        queryset = EmotionRecord.objects.filter(user=request.user, recorded_at__gte=start_at, recorded_at__lte=end_at)
        payload = _emotion_report_payload(queryset, start_at, end_at, request=request)
        payload["start_date"] = start_day.isoformat()
        payload["end_date"] = end_day.isoformat()
        return APIResponse.success(data=payload)


class UserEmotionAnalysisCorrectView(APIView):
    authentication_classes = [UserJWTAuthentication]
    permission_classes = [IsAppUserAuthenticated]

    def post(self, request, analysis_pk):
        analysis = EmotionAnalysis.objects.select_related("record").filter(pk=analysis_pk, record__user=request.user).first()
        if analysis is None:
            raise Http404("Emotion analysis does not exist.")

        corrected_label = (request.data.get("corrected_label") or "").strip()
        accepted = _parse_bool_value(request.data.get("accepted"))
        note = (request.data.get("note") or "").strip()

        if corrected_label and not EmotionTag.objects.filter(code=corrected_label).exists():
            raise ValidationError({"corrected_label": "Unsupported emotion label."})
        if accepted is None and not corrected_label:
            raise ValidationError({"accepted": "Provide accepted=false or a corrected_label."})

        feedback = _save_analysis_feedback(analysis, corrected_label, accepted, note)
        log_feature_usage(
            feature="emotion_analysis",
            action="correction_submitted",
            user_id=str(request.user.pk),
            metadata={
                "record_id": analysis.record_id,
                "analysis_id": analysis.id,
                "predicted_label": analysis.predicted_label,
                "corrected_label": corrected_label,
                "accepted": feedback["accepted"],
                "source": "user_analysis_endpoint",
            },
        )
        return APIResponse.success(data={"analysis_id": analysis.id, "feedback_saved": True, "feedback": feedback})


class UserEmotionGrowthCurveView(APIView):
    authentication_classes = [UserJWTAuthentication]
    permission_classes = [IsAppUserAuthenticated]

    def get(self, request):
        serializer = TimelineQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data

        range_key = (request.query_params.get("range") or "").strip().lower()
        days = params["days"] if "days" in request.query_params else (30 if range_key == "month" else 7)
        try:
            window = resolve_date_window(
                days=days,
                start_date=params.get("start_date"),
                end_date=params.get("end_date"),
            )
        except ValueError as exc:
            raise ValidationError({"date": str(exc)}) from exc

        drilldown = None
        if params.get("date"):
            try:
                drilldown = _growth_curve_drilldown(request.user, params["date"])
            except ValueError as exc:
                raise ValidationError({"date": str(exc)}) from exc

        payload = _growth_curve_payload(request.user, window, drilldown=drilldown)
        action = "refresh" if params.get("refresh") else "view"
        if drilldown is not None and action == "view":
            action = "drilldown_view"
        log_feature_usage(
            feature="emotion_growth_curve",
            action=action,
            user_id=str(request.user.pk),
            metadata={
                "start_date": payload["start_date"],
                "end_date": payload["end_date"],
                "range": range_key or "",
                "drilldown_date": drilldown["date"] if drilldown else "",
                "record_count": payload["summary"]["record_count"],
            },
        )
        return APIResponse.success(
            data=payload
        )


class UserDeviceTokenView(APIView):
    authentication_classes = [UserJWTAuthentication]
    permission_classes = [IsAppUserAuthenticated]

    def get(self, request):
        devices = request.user.device_tokens.order_by("-updated_at", "-id")
        return APIResponse.success(data=UserDeviceTokenSerializer(devices, many=True).data)

    def post(self, request):
        serializer = UserDeviceTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device = register_device_token(user=request.user, **serializer.validated_data)
        log_feature_usage("device_token", action="register", user_id=str(request.user.pk), metadata={"device_id": device.id})
        return APIResponse.success(data=UserDeviceTokenSerializer(device).data, message="registered")


class UserReminderPreferenceView(APIView):
    authentication_classes = [UserJWTAuthentication]
    permission_classes = [IsAppUserAuthenticated]

    def get(self, request):
        preference = get_or_create_reminder_preference(request.user)
        return APIResponse.success(data=UserReminderPreferenceSerializer(preference).data)

    def patch(self, request):
        preference = get_or_create_reminder_preference(request.user)
        serializer = UserReminderPreferenceSerializer(preference, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_feature_usage("emotion_reminder", action="preference_update", user_id=str(request.user.pk))
        return APIResponse.success(data=UserReminderPreferenceSerializer(preference).data)


class UserReminderTriggerView(APIView):
    authentication_classes = [UserJWTAuthentication]
    permission_classes = [IsAppUserAuthenticated]

    def post(self, request):
        logs = trigger_user_reminder(request.user)
        return APIResponse.success(data=ReminderDispatchLogSerializer(logs, many=True).data, message="triggered")


class UserEmotionExportView(APIView):
    authentication_classes = [UserJWTAuthentication]
    permission_classes = [IsAppUserAuthenticated]

    def get(self, request):
        tasks = request.user.export_tasks.order_by("-created_at", "-id")
        return APIResponse.success(data=EmotionExportTaskSerializer(tasks, many=True).data)

    def post(self, request):
        serializer = EmotionExportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = create_export_task(user=request.user, **serializer.validated_data)
        log_feature_usage(
            "emotion_export",
            action="create",
            user_id=str(request.user.pk),
            metadata={"task_id": task.id, "format": task.file_format, "record_count": task.record_count},
        )
        payload = {
            **EmotionExportTaskSerializer(task).data,
            "content": task.content,
        }
        return APIResponse.success(data=payload, status_code=status.HTTP_201_CREATED, message="exported")


class UserEmotionExportDownloadView(APIView):
    authentication_classes = [UserJWTAuthentication]
    permission_classes = [IsAppUserAuthenticated]

    def get(self, request, task_id):
        task = request.user.export_tasks.filter(pk=task_id).first()
        if task is None:
            raise Http404("Export task does not exist.")
        if task.status != EmotionDataExportTask.Status.COMPLETED:
            raise ValidationError({"task_id": "Export task is not ready."})
        return APIResponse.success(
            data={
                "id": task.id,
                "file_name": task.file_name,
                "file_format": task.file_format,
                "content": task.content,
                "record_count": task.record_count,
            }
        )


def _growth_curve_payload(user, window, drilldown=None):
    start_day, end_day, start_at, end_at = window
    records = list(
        EmotionRecord.objects.select_related("tag", "analysis")
        .filter(user=user, recorded_at__gte=start_at, recorded_at__lte=end_at)
        .order_by("recorded_at", "id")
    )

    grouped = {}
    for record in records:
        grouped.setdefault(timezone.localtime(record.recorded_at).date(), []).append(record)

    series = []
    previous_score = None
    current = start_day
    while current <= end_day:
        point = _growth_curve_point(current, grouped.get(current, []))
        point["delta"] = None if previous_score is None else round(point["score"] - previous_score, 1)
        previous_score = point["score"]
        series.append(point)
        current += timedelta(days=1)

    payload = {
        "start_date": start_day.isoformat(),
        "end_date": end_day.isoformat(),
        "days": len(series),
        "summary": _growth_curve_summary(records, series),
        "series": series,
    }
    if drilldown is not None:
        payload["drilldown"] = drilldown
    return payload


def _growth_curve_point(day, records):
    label_counts = Counter()
    scores = []
    intensities = []
    valence_counts = {"positive": 0, "negative": 0, "neutral": 0}

    for record in records:
        try:
            analysis = record.analysis
        except EmotionAnalysis.DoesNotExist:
            analysis = None
        label = analysis.predicted_label if analysis and analysis.predicted_label else record.tag.code
        intensity = analysis.intensity if analysis else 0
        detail = emotion_presentation(label)
        label_counts[label] += 1
        valence_counts[detail["valence"]] += 1
        scores.append(emotion_growth_score(label, intensity))
        intensities.append(intensity)

    dominant_label = label_counts.most_common(1)[0][0] if label_counts else None
    total = sum(label_counts.values()) or 1
    return {
        "date": day.isoformat(),
        "score": round(sum(scores) / len(scores), 1) if scores else 50.0,
        "average_intensity": round(sum(intensities) / len(intensities), 1) if intensities else 0.0,
        "record_count": len(records),
        "dominant_emotion": emotion_presentation(dominant_label) if dominant_label else None,
        "emotion_breakdown": [
            {
                **emotion_presentation(label),
                "count": count,
                "ratio": round(count / total, 4),
            }
            for label, count in label_counts.most_common()
        ],
        "positive_count": valence_counts["positive"],
        "negative_count": valence_counts["negative"],
        "neutral_count": valence_counts["neutral"],
    }


def _growth_curve_summary(records, series):
    label_counts = Counter()
    scores = []
    for record in records:
        try:
            analysis = record.analysis
        except EmotionAnalysis.DoesNotExist:
            analysis = None
        label = analysis.predicted_label if analysis and analysis.predicted_label else record.tag.code
        intensity = analysis.intensity if analysis else 0
        label_counts[label] += 1
        scores.append(emotion_growth_score(label, intensity))

    trend = EmotionAnalysis.TREND_STABLE
    active_points = [point for point in series if point["record_count"]]
    if len(active_points) >= 2:
        delta = active_points[-1]["score"] - active_points[0]["score"]
        if delta >= 8:
            trend = EmotionAnalysis.TREND_RISING
        elif delta <= -8:
            trend = EmotionAnalysis.TREND_FALLING

    dominant_label = label_counts.most_common(1)[0][0] if label_counts else None
    return {
        "record_count": len(records),
        "average_score": round(sum(scores) / len(scores), 1) if scores else 50.0,
        "dominant_emotion": emotion_presentation(dominant_label) if dominant_label else None,
        "trend": trend,
    }


def _growth_curve_drilldown(user, day):
    target_day, start_at, end_at = resolve_day_window(day)
    records = (
        EmotionRecord.objects.select_related("tag", "analysis")
        .filter(user=user, recorded_at__gte=start_at, recorded_at__lte=end_at)
        .order_by("-recorded_at", "-id")
    )
    details = []
    for record in records:
        try:
            analysis = record.analysis
        except EmotionAnalysis.DoesNotExist:
            analysis = None
        label = analysis.predicted_label if analysis and analysis.predicted_label else record.tag.code
        intensity = analysis.intensity if analysis else 0
        details.append(
            {
                "id": record.id,
                "recorded_at": timezone.localtime(record.recorded_at).isoformat(),
                "emotion_text": decrypt_text(record.emotion_text, is_encrypted=record.is_encrypted),
                "source": record.source,
                "is_collect": record.is_collect,
                "tag": emotion_presentation(record.tag.code),
                "analysis_label": emotion_presentation(label),
                "intensity": intensity,
                "score": emotion_growth_score(label, intensity),
            }
        )

    return {
        "date": target_day.isoformat(),
        "record_count": len(details),
        "records": details,
    }


class EmotionAnalysisByRecordView(APIView):
    def get(self, request, record_pk):
        try:
            analysis = EmotionAnalysis.objects.select_related("record", "record__user", "record__tag").get(record_id=record_pk)
        except EmotionAnalysis.DoesNotExist as exc:
            raise Http404("Emotion analysis does not exist for this record.") from exc

        serializer = EmotionAnalysisSerializer(analysis)
        return Response(serializer.data)
