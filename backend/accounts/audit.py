import logging

from django.apps import apps


logger = logging.getLogger(__name__)


def log_admin_operation(admin_user, action, request=None, detail="", metadata=None):
    try:
        log_model = apps.get_model("analytics", "AdminOperationLog")
    except LookupError:
        return

    try:
        payload = _build_payload(log_model, admin_user, action, request, detail, metadata or {})
        log_model.objects.create(**payload)
    except Exception:
        logger.exception("Failed to write admin operation log.")


def _build_payload(log_model, admin_user, action, request, detail, metadata):
    field_names = {field.name for field in log_model._meta.fields}
    payload = {}

    if admin_user is not None and "admin_user" in field_names:
        payload["admin_user"] = admin_user
    if admin_user is not None and "user" in field_names:
        payload["user"] = admin_user
    if admin_user is not None and "admin_user_id" in field_names:
        payload["admin_user_id"] = admin_user.pk
    if "username" in field_names:
        payload["username"] = getattr(admin_user, "username", "") or metadata.get("username", "")

    if "action" in field_names:
        payload["action"] = action
    if "operation" in field_names:
        payload["operation"] = action
    if "operation_type" in field_names:
        payload["operation_type"] = action

    if "detail" in field_names:
        payload["detail"] = detail
    if "description" in field_names:
        payload["description"] = detail
    if "metadata" in field_names:
        payload["metadata"] = metadata

    if request is not None:
        ip_address = _get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        if "ip_address" in field_names:
            payload["ip_address"] = ip_address
        if "ip" in field_names:
            payload["ip"] = ip_address
        if "user_agent" in field_names:
            payload["user_agent"] = user_agent

    return payload


def _get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")
