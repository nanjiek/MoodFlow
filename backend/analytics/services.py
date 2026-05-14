import hashlib
import json
import logging
from datetime import date, datetime, time, timedelta

from django.apps import apps
from django.core.cache import cache
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.utils.dateparse import parse_date

from .models import AdminOperationLog, FeatureUsageLog


logger = logging.getLogger(__name__)

STATISTICS_CACHE_TIMEOUT = 20 * 60


def log_admin_operation(
    admin_user=None,
    action="",
    target_type="",
    target_id="",
    request=None,
    metadata=None,
    admin_id=None,
    admin_username="",
    ip_address=None,
):
    try:
        actor = admin_user or getattr(request, "user", None)
        resolved_admin_id = admin_id if admin_id is not None else getattr(actor, "pk", None)
        resolved_username = admin_username or getattr(actor, "username", "") or ""

        return AdminOperationLog.objects.create(
            admin_id=_coerce_positive_int(resolved_admin_id),
            admin_username=_truncate(resolved_username, 150),
            action=_truncate(action, 100),
            target_type=_truncate(target_type, 100),
            target_id=_truncate(target_id, 100),
            ip_address=ip_address or _get_client_ip(request) or None,
            metadata=metadata or {},
        )
    except Exception:
        logger.exception("Failed to write admin operation log.")
        return None


def log_feature_usage(feature, user_id="", action="view", metadata=None, user=None, request=None):
    try:
        resolved_user_id = user_id
        if resolved_user_id in (None, "") and user is not None:
            resolved_user_id = getattr(user, "pk", "")
        if resolved_user_id in (None, "") and request is not None:
            resolved_user_id = getattr(getattr(request, "user", None), "pk", "")

        return FeatureUsageLog.objects.create(
            feature=_truncate(feature, 80),
            user_id=_truncate(resolved_user_id, 64),
            action=_truncate(action, 80),
            metadata=metadata or {},
        )
    except Exception:
        logger.exception("Failed to write feature usage log.")
        return None


def overview():
    return _cached_statistics("overview", {}, _build_overview, timeout=STATISTICS_CACHE_TIMEOUT)


def active_users(days=30, start_date=None, end_date=None):
    window = _resolve_date_window(days=days, start_date=start_date, end_date=end_date)
    return _cached_statistics(
        "active_users",
        _window_cache_params(window),
        lambda: _build_active_users(window),
        timeout=STATISTICS_CACHE_TIMEOUT,
    )


def emotion_distribution(days=30, start_date=None, end_date=None):
    window = _resolve_date_window(days=days, start_date=start_date, end_date=end_date)
    return _cached_statistics(
        "emotion_distribution",
        _window_cache_params(window),
        lambda: _build_emotion_distribution(window),
        timeout=STATISTICS_CACHE_TIMEOUT,
    )


def feature_usage(days=30, start_date=None, end_date=None, feature=None, action=None):
    window = _resolve_date_window(days=days, start_date=start_date, end_date=end_date)
    params = {
        **_window_cache_params(window),
        "feature": feature or "",
        "action": action or "",
    }
    return _cached_statistics(
        "feature_usage",
        params,
        lambda: _build_feature_usage(window, feature=feature, action=action),
        timeout=STATISTICS_CACHE_TIMEOUT,
    )


def resolve_date_window(days=30, start_date=None, end_date=None):
    return _resolve_date_window(days=days, start_date=start_date, end_date=end_date)


def resolve_day_window(day):
    day_value = _coerce_date(day)
    if day_value is None:
        raise ValueError("Use YYYY-MM-DD for the drill-down date.")
    return day_value, _day_start(day_value), _day_end(day_value)


def _build_overview():
    now = timezone.now()
    today_start = _day_start(timezone.localdate())
    last_7_days = now - timedelta(days=7)

    total_users = _model_count("emotions", "AppUser")
    emotion_record_model = _get_model("emotions", "EmotionRecord")
    tree_hole_post_model = _get_model("moderation", "TreeHolePost")

    emotion_records_total = emotion_record_model.objects.count() if emotion_record_model else 0
    emotion_records_today = (
        emotion_record_model.objects.filter(recorded_at__gte=today_start).count()
        if emotion_record_model
        else 0
    )
    tree_hole_posts_total = tree_hole_post_model.objects.count() if tree_hole_post_model else 0

    feature_events_total = FeatureUsageLog.objects.count()
    feature_events_today = FeatureUsageLog.objects.filter(created_at__gte=today_start).count()
    active_users_7d = (
        FeatureUsageLog.objects.filter(created_at__gte=last_7_days)
        .exclude(user_id="")
        .values("user_id")
        .distinct()
        .count()
    )
    top_feature = (
        FeatureUsageLog.objects.values("feature")
        .annotate(count=Count("id"))
        .order_by("-count", "feature")
        .first()
    )

    return {
        "generated_at": now.isoformat(),
        "total_users": total_users,
        "active_users_7d": active_users_7d,
        "emotion_records_total": emotion_records_total,
        "emotion_records_today": emotion_records_today,
        "feature_events_total": feature_events_total,
        "feature_events_today": feature_events_today,
        "admin_operation_logs_total": AdminOperationLog.objects.count(),
        "tree_hole_posts_total": tree_hole_posts_total,
        "top_feature": top_feature or {},
    }


def _build_active_users(window):
    start_day, end_day, start_at, end_at = window
    queryset = FeatureUsageLog.objects.filter(created_at__gte=start_at, created_at__lte=end_at).exclude(user_id="")
    rows = (
        queryset.annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(active_users=Count("user_id", distinct=True), events=Count("id"))
        .order_by("day")
    )
    by_day = {row["day"]: row for row in rows}

    series = []
    for day in _iter_days(start_day, end_day):
        row = by_day.get(day, {})
        series.append(
            {
                "date": day.isoformat(),
                "active_users": row.get("active_users", 0),
                "events": row.get("events", 0),
            }
        )

    return {
        "start_date": start_day.isoformat(),
        "end_date": end_day.isoformat(),
        "days": len(series),
        "total_active_users": queryset.values("user_id").distinct().count(),
        "total_events": queryset.count(),
        "series": series,
    }


def _build_emotion_distribution(window):
    start_day, end_day, start_at, end_at = window
    emotion_record_model = _get_model("emotions", "EmotionRecord")
    if emotion_record_model is None:
        return _empty_distribution(start_day, end_day)

    queryset = emotion_record_model.objects.filter(recorded_at__gte=start_at, recorded_at__lte=end_at)
    total = queryset.count()
    rows = (
        queryset.values("tag_id", "tag__code", "tag__name")
        .annotate(count=Count("id"))
        .order_by("-count", "tag__code")
    )

    distribution = []
    for row in rows:
        count = row["count"]
        distribution.append(
            {
                "tag_id": row["tag_id"],
                "code": row["tag__code"],
                "name": row["tag__name"],
                "count": count,
                "ratio": round(count / total, 4) if total else 0,
            }
        )

    return {
        "start_date": start_day.isoformat(),
        "end_date": end_day.isoformat(),
        "total": total,
        "distribution": distribution,
    }


def _build_feature_usage(window, feature=None, action=None):
    start_day, end_day, start_at, end_at = window
    queryset = FeatureUsageLog.objects.filter(created_at__gte=start_at, created_at__lte=end_at)
    if feature:
        queryset = queryset.filter(feature=feature)
    if action:
        queryset = queryset.filter(action=action)

    event_rows = (
        queryset.values("feature", "action")
        .annotate(
            count=Count("id"),
            unique_users=Count("user_id", filter=~Q(user_id=""), distinct=True),
        )
        .order_by("-count", "feature", "action")
    )
    feature_rows = (
        queryset.values("feature")
        .annotate(
            count=Count("id"),
            unique_users=Count("user_id", filter=~Q(user_id=""), distinct=True),
        )
        .order_by("-count", "feature")
    )

    return {
        "start_date": start_day.isoformat(),
        "end_date": end_day.isoformat(),
        "total_events": queryset.count(),
        "total_unique_users": queryset.exclude(user_id="").values("user_id").distinct().count(),
        "by_feature": list(feature_rows),
        "by_action": list(event_rows),
    }


def _cached_statistics(name, params, builder, timeout):
    cache_key = _cache_key(name, params)
    try:
        cached_value = cache.get(cache_key)
    except Exception:
        logger.warning("Statistics cache read failed; falling back to database.", exc_info=True)
        return builder()

    if cached_value is not None:
        return cached_value

    value = builder()
    try:
        cache.set(cache_key, value, timeout=timeout)
    except Exception:
        logger.warning("Statistics cache write failed.", exc_info=True)
    return value


def _cache_key(name, params):
    payload = json.dumps(params, sort_keys=True, default=str, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"analytics:statistics:{name}:{digest}"


def _resolve_date_window(days=30, start_date=None, end_date=None):
    end_day = _coerce_date(end_date) or timezone.localdate()
    start_day = _coerce_date(start_date)
    if start_day is None:
        days = _coerce_days(days)
        start_day = end_day - timedelta(days=days - 1)
    if start_day > end_day:
        raise ValueError("start_date must be earlier than or equal to end_date.")
    return start_day, end_day, _day_start(start_day), _day_end(end_day)


def _coerce_date(value):
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return timezone.localdate(value)
    if isinstance(value, date):
        return value
    parsed = parse_date(str(value))
    if parsed is None:
        raise ValueError("Use YYYY-MM-DD for date filters.")
    return parsed


def _coerce_days(value):
    try:
        days = int(value)
    except (TypeError, ValueError):
        days = 30
    return min(max(days, 1), 366)


def _day_start(day):
    return timezone.make_aware(datetime.combine(day, time.min), timezone.get_current_timezone())


def _day_end(day):
    return timezone.make_aware(datetime.combine(day, time.max), timezone.get_current_timezone())


def _iter_days(start_day, end_day):
    current = start_day
    while current <= end_day:
        yield current
        current += timedelta(days=1)


def _window_cache_params(window):
    start_day, end_day, _, _ = window
    return {
        "start_date": start_day.isoformat(),
        "end_date": end_day.isoformat(),
    }


def _get_model(app_label, model_name):
    try:
        return apps.get_model(app_label, model_name)
    except (LookupError, RuntimeError):
        return None


def _model_count(app_label, model_name):
    model = _get_model(app_label, model_name)
    return model.objects.count() if model else 0


def _empty_distribution(start_day, end_day):
    return {
        "start_date": start_day.isoformat(),
        "end_date": end_day.isoformat(),
        "total": 0,
        "distribution": [],
    }


def _get_client_ip(request):
    if request is None:
        return ""
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def _truncate(value, max_length):
    if value is None:
        value = ""
    value = str(value)
    return value[:max_length]


def _coerce_positive_int(value):
    if value in (None, ""):
        return None
    try:
        value = int(value)
    except (TypeError, ValueError):
        return None
    return value if value >= 0 else None
