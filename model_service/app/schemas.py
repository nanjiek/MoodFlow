from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EmotionPredictRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    selected_label: str | None = None
    user_id: str | None = None


class EmotionPredictResponse(BaseModel):
    label: str
    label_name: str
    display_name: str
    display_hint: str
    category: str
    confidence: float
    intensity: float
    keywords: list[str]
    explanation: str
    gentle_feedback: str
    recommended_content_types: list[str]
    suggested_prompt: str
    model_version: str
    probabilities: dict[str, float]


class KeywordRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(8, ge=1, le=20)


class KeywordResponse(BaseModel):
    keywords: list[str]


class TrendRequest(BaseModel):
    records: list[dict[str, Any]] = Field(default_factory=list)


class TrendResponse(BaseModel):
    trend: str
    summary: str
    dominant_label: str | None = None
    negative_days: int = 0
    highlights: list[str] = Field(default_factory=list)
    next_suggestion: str = ""
