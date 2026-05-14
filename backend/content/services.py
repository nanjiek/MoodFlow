from django.apps import apps
from django.db.models import Case, IntegerField, Q, Value, When

from .models import CompanionContent


def _emotion_tag_fields():
    try:
        emotion_tag_model = apps.get_model("emotions", "EmotionTag")
    except LookupError:
        return set()
    return {field.name for field in emotion_tag_model._meta.fields}


def _build_emotion_tag_query(value):
    fields = _emotion_tag_fields()
    query = Q()

    if value is None:
        return query

    value = str(value).strip()
    if not value:
        return query

    if value.isdigit():
        query |= Q(emotion_tag_id=int(value))
    for field_name in ("code", "slug", "name", "label"):
        if field_name in fields:
            query |= Q(**{f"emotion_tag__{field_name}": value})
    return query


def _content_type_rank(preferred_types):
    if not preferred_types:
        return None

    if isinstance(preferred_types, str):
        preferred_types = preferred_types.split(",")

    choices = {choice for choice, _ in CompanionContent.CONTENT_TYPE_CHOICES}
    ordered_types = []
    for content_type in preferred_types:
        content_type = str(content_type).strip()
        if content_type in choices and content_type not in ordered_types:
            ordered_types.append(content_type)

    if not ordered_types:
        return None

    return Case(
        *[
            When(content_type=content_type, then=Value(rank))
            for rank, content_type in enumerate(ordered_types)
        ],
        default=Value(len(ordered_types)),
        output_field=IntegerField(),
    )


def recommend_contents(emotion_code, limit=5, preferred_types=None):
    """Return active companion content ranked by emotion match, type preference, and weight."""
    if limit is None:
        limit = 5
    limit = max(int(limit), 0)
    if limit == 0:
        return []

    queryset = CompanionContent.objects.select_related("emotion_tag").filter(is_active=True)

    emotion_query = _build_emotion_tag_query(emotion_code)
    if emotion_query:
        queryset = queryset.filter(emotion_query | Q(emotion_tag__isnull=True))

    annotations = {}
    order_by = []

    if emotion_query:
        annotations["_emotion_rank"] = Case(
            When(emotion_query, then=Value(0)),
            When(emotion_tag__isnull=True, then=Value(1)),
            default=Value(2),
            output_field=IntegerField(),
        )
        order_by.append("_emotion_rank")

    type_rank = _content_type_rank(preferred_types or [])
    if type_rank is not None:
        annotations["_type_rank"] = type_rank
        order_by.append("_type_rank")

    if annotations:
        queryset = queryset.annotate(**annotations)

    order_by.extend(["-weight", "id"])
    return list(queryset.order_by(*order_by)[:limit])
