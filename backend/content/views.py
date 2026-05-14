from django.apps import apps
from django.db.models import Q
from rest_framework import mixins, viewsets
from rest_framework.exceptions import ValidationError

from .models import CompanionContent, SystemConfig
from .serializers import CompanionContentSerializer, SystemConfigSerializer


TRUE_VALUES = {"1", "true", "t", "yes", "y", "on"}
FALSE_VALUES = {"0", "false", "f", "no", "n", "off"}


def _parse_bool(value, field_name):
    if value is None or value == "":
        return None

    normalized = str(value).strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    raise ValidationError({field_name: "Expected a boolean value."})


def _emotion_tag_fields():
    try:
        emotion_tag_model = apps.get_model("emotions", "EmotionTag")
    except LookupError:
        return set()
    return {field.name for field in emotion_tag_model._meta.fields}


def _build_emotion_tag_query(value):
    value = str(value).strip()
    if not value:
        return Q()

    fields = _emotion_tag_fields()
    query = Q()
    if value.isdigit():
        query |= Q(emotion_tag_id=int(value))
    for field_name in ("code", "slug", "name", "label"):
        if field_name in fields:
            query |= Q(**{f"emotion_tag__{field_name}": value})
    return query


class CompanionContentViewSet(viewsets.ModelViewSet):
    serializer_class = CompanionContentSerializer
    queryset = CompanionContent.objects.select_related("emotion_tag").all()

    def get_queryset(self):
        return super().get_queryset()

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        params = self.request.query_params

        for filter_name in ("emotion", "tag"):
            tag_value = params.get(filter_name)
            if not tag_value:
                continue
            tag_query = _build_emotion_tag_query(tag_value)
            queryset = queryset.filter(tag_query) if tag_query else queryset.none()

        content_type = params.get("type") or params.get("content_type")
        if content_type:
            requested_types = {
                item.strip()
                for item in content_type.split(",")
                if item.strip()
            }
            allowed_types = {choice for choice, _ in CompanionContent.CONTENT_TYPE_CHOICES}
            invalid_types = requested_types - allowed_types
            if invalid_types:
                raise ValidationError({"type": f"Unsupported content type: {', '.join(sorted(invalid_types))}."})
            if requested_types:
                queryset = queryset.filter(content_type__in=requested_types)

        is_active = _parse_bool(params.get("is_active"), "is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)

        return queryset


class SystemConfigViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = SystemConfigSerializer
    queryset = SystemConfig.objects.all()
    lookup_field = "key"
    lookup_value_regex = "[^/]+"
    http_method_names = ["get", "put", "patch", "head", "options"]
