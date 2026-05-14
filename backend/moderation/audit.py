import json

from django.apps import apps
from django.db import models


def write_admin_operation_log(request, action, post, reason=""):
    try:
        operation_log = apps.get_model("analytics", "AdminOperationLog")
    except (LookupError, RuntimeError):
        return

    try:
        operation_log.objects.create(**_build_log_kwargs(operation_log, request, action, post, reason))
    except Exception:
        return


def _build_log_kwargs(operation_log, request, action, post, reason):
    fields = {field.name: field for field in operation_log._meta.fields}
    actor = getattr(request, "user", None)
    actor_id = getattr(actor, "pk", None)
    actor_label = _actor_label(actor)
    detail = {
        "action": action,
        "post_id": post.pk,
        "status": post.status,
        "reason": reason,
        "operator": actor_label,
    }
    kwargs = {}

    _set_first(kwargs, fields, ("action", "operation", "operation_type", "event"), action)
    _set_first(kwargs, fields, ("target_type", "object_type", "resource_type"), "tree_hole_post")
    _set_first(kwargs, fields, ("target_id", "object_id", "resource_id"), str(post.pk))
    _set_first(kwargs, fields, ("target_name", "object_name", "resource_name"), f"TreeHolePost#{post.pk}")
    _set_first(kwargs, fields, ("detail", "details", "metadata", "extra", "payload"), detail)
    _set_first(kwargs, fields, ("operator_name", "admin_name"), actor_label)

    for field_name in ("post_id", "tree_hole_post_id"):
        if field_name in fields:
            kwargs[field_name] = post.pk

    for field_name in ("operator_id", "admin_id", "user_id"):
        if field_name in fields and actor_id is not None:
            kwargs[field_name] = actor_id

    for field_name in ("operator", "admin", "user"):
        if field_name in fields and field_name not in kwargs:
            value = _coerce_actor_value(fields[field_name], actor, actor_label)
            if value is not None:
                kwargs[field_name] = value

    return kwargs


def _set_first(kwargs, fields, names, value):
    for name in names:
        if name in fields and name not in kwargs:
            kwargs[name] = _coerce_field_value(fields[name], value)
            return


def _coerce_actor_value(field, actor, actor_label):
    if field.remote_field and actor is not None:
        remote_model = field.remote_field.model
        if isinstance(actor, remote_model):
            return actor
        actor_id = getattr(actor, "pk", None)
        if actor_id is not None:
            try:
                return remote_model.objects.filter(pk=actor_id).first()
            except Exception:
                return None
    if isinstance(field, models.CharField):
        return actor_label
    return None


def _coerce_field_value(field, value):
    if isinstance(field, models.JSONField):
        return value
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(field, (models.IntegerField, models.BigIntegerField)):
        try:
            return int(value)
        except (TypeError, ValueError):
            return value
    return value


def _actor_label(actor):
    if not actor or getattr(actor, "is_anonymous", False):
        return ""
    for attr in ("username", "name", "email", "mobile", "phone"):
        value = getattr(actor, attr, None)
        if value:
            return str(value)
    actor_id = getattr(actor, "pk", None)
    return str(actor_id) if actor_id is not None else str(actor)
