from __future__ import annotations

from typing import Any

from rest_framework import status
from rest_framework.response import Response


class APIResponse:
    """统一 API 响应结构。"""

    @staticmethod
    def success(
        data: Any = None,
        message: str = "success",
        code: int | str = 0,
        status_code: int = status.HTTP_200_OK,
        **extra: Any,
    ) -> Response:
        payload = {
            "code": code,
            "message": message,
            "data": {} if data is None else data,
        }
        payload.update(extra)
        return Response(payload, status=status_code)

    @staticmethod
    def error(
        message: str = "error",
        code: int | str = -1,
        data: Any = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        **extra: Any,
    ) -> Response:
        payload = {
            "code": code,
            "message": message,
            "data": {} if data is None else data,
        }
        payload.update(extra)
        return Response(payload, status=status_code)
