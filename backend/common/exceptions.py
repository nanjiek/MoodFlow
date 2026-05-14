from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.views import exception_handler

from .response import APIResponse


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        message, errors = normalize_error_payload(response.data)
        code = getattr(exc, "default_code", "error")
        return APIResponse.error(
            message=message,
            code=str(code),
            data=errors,
            status_code=response.status_code,
        )

    if isinstance(exc, DjangoValidationError):
        return APIResponse.error(
            message="validation error",
            code="validation_error",
            data=exc.message_dict if hasattr(exc, "message_dict") else exc.messages,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    message = str(exc) if settings.DEBUG else "internal server error"
    return APIResponse.error(
        message=message,
        code="server_error",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def normalize_error_payload(payload):
    if isinstance(payload, dict):
        detail = payload.get("detail")
        if detail is not None:
            return str(detail), {}
        return "validation error", payload
    if isinstance(payload, list):
        return "validation error", payload
    return str(payload), {}
