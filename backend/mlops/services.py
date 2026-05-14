from __future__ import annotations

import hashlib
import logging
import os
import time
from typing import Any

import requests
from django.conf import settings
from django.db import DatabaseError

from .models import InferenceLog, ModelVersion


logger = logging.getLogger(__name__)

DEFAULT_MODEL_SERVICE_URL = "http://localhost:8010"
DEFAULT_MODEL_SERVICE_TIMEOUT = 3

MOODFLOW_LABELS = (
    "happy",
    "calm",
    "expecting",
    "anxious",
    "sad",
    "irritable",
    "plain",
    "tired",
)

LABEL_NAMES = {
    "happy": "开心",
    "calm": "平静",
    "expecting": "期待",
    "anxious": "焦虑",
    "sad": "难过",
    "irritable": "烦躁",
    "plain": "平淡",
    "tired": "疲惫",
}

KEYWORD_MAP = {
    "happy": ("开心", "快乐", "幸福", "满足", "顺利", "喜欢", "哈哈", "成功"),
    "calm": ("平静", "放松", "安宁", "舒服", "淡然", "舒缓"),
    "expecting": ("期待", "盼望", "希望", "想要", "等着", "兴奋"),
    "anxious": ("焦虑", "紧张", "担心", "害怕", "不安", "压力", "迷茫", "恐惧"),
    "sad": ("难过", "伤心", "委屈", "失落", "沮丧", "低落", "想哭"),
    "irritable": ("烦", "生气", "愤怒", "火大", "不爽", "讨厌", "烦躁"),
    "plain": ("普通", "平淡", "没感觉", "一般", "日常"),
    "tired": ("疲惫", "累", "困", "没精神", "乏力", "熬夜"),
}


def get_model_service_url() -> str:
    return str(getattr(settings, "MODEL_SERVICE_URL", os.getenv("MODEL_SERVICE_URL", DEFAULT_MODEL_SERVICE_URL))).rstrip("/")


def call_model_service(text: str, selected_label: str | None = None) -> dict[str, Any]:
    """Call the model service and persist one inference log, falling back to rules on failure."""

    started_at = time.perf_counter()
    request_source = "model_service"
    normalized_text = text or ""
    payload = {"text": normalized_text, "selected_label": selected_label}

    if not normalized_text.strip() and selected_label:
        result = _rule_based_fallback(normalized_text, selected_label, "blank text shortcut")
        latency_ms = int((time.perf_counter() - started_at) * 1000)
        _create_inference_log(normalized_text, result, latency_ms, "rule_fallback")
        return result

    try:
        response = requests.post(
            f"{get_model_service_url()}/predict/emotion",
            json=payload,
            timeout=_model_service_timeout(),
        )
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict) or not result.get("label"):
            raise ValueError("Model service returned an invalid prediction payload.")
    except (requests.RequestException, ValueError) as exc:
        request_source = "rule_fallback"
        result = _rule_based_fallback(text, selected_label, str(exc))

    latency_ms = int((time.perf_counter() - started_at) * 1000)
    _create_inference_log(text, result, latency_ms, request_source)
    return result


def _model_service_timeout() -> float:
    raw_timeout = getattr(settings, "MODEL_SERVICE_TIMEOUT", os.getenv("MODEL_SERVICE_TIMEOUT", DEFAULT_MODEL_SERVICE_TIMEOUT))
    try:
        return float(raw_timeout)
    except (TypeError, ValueError):
        return float(DEFAULT_MODEL_SERVICE_TIMEOUT)


def _create_inference_log(text: str, result: dict[str, Any], latency_ms: int, request_source: str) -> None:
    try:
        InferenceLog.objects.create(
            text_hash=hashlib.sha256((text or "").encode("utf-8")).hexdigest(),
            predicted_label=str(result.get("label") or result.get("predicted_label") or "plain")[:64],
            confidence=_bounded_float(result.get("confidence"), default=0),
            model_version=str(result.get("model_version") or "")[:64],
            latency_ms=max(0, latency_ms),
            request_source=request_source,
            raw_result=result,
        )
    except DatabaseError:
        logger.exception("Failed to persist inference log.")


def _rule_based_fallback(text: str, selected_label: str | None, error: str) -> dict[str, Any]:
    normalized_text = (text or "").strip()
    scores = {label: 0.02 for label in MOODFLOW_LABELS}
    matched_keywords: list[str] = []

    for label, keywords in KEYWORD_MAP.items():
        for keyword in keywords:
            if keyword in normalized_text:
                scores[label] += 0.28
                matched_keywords.append(keyword)

    if selected_label in scores:
        scores[selected_label] += 0.2

    total = sum(scores.values()) or 1
    probabilities = {label: score / total for label, score in scores.items()}
    label = max(probabilities, key=probabilities.get)
    confidence = probabilities[label]
    active_version = ""
    try:
        active_version = ModelVersion.objects.filter(is_active=True).values_list("version", flat=True).first() or ""
    except DatabaseError:
        logger.exception("Failed to read active model version for fallback prediction.")

    return {
        "label": label,
        "label_name": LABEL_NAMES.get(label, LABEL_NAMES["plain"]),
        "category": _label_category(label),
        "confidence": round(float(confidence), 4),
        "intensity": round(min(1.0, max(0.25, confidence + 0.05 * len(matched_keywords))), 4),
        "keywords": matched_keywords[:8],
        "model_version": active_version or "rule-fallback",
        "probabilities": {key: round(float(value), 4) for key, value in probabilities.items()},
        "fallback": True,
        "error": error,
    }


def _bounded_float(value: Any, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = default
    return min(1.0, max(0.0, parsed))


def _label_category(label: str) -> str:
    if label in {"happy", "calm", "expecting"}:
        return "positive"
    if label in {"anxious", "sad", "irritable", "tired"}:
        return "negative"
    return "neutral"
