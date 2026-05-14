from __future__ import annotations

from fastapi import FastAPI

from model_service.app.predictor import EmotionPredictor, analyze_trend
from model_service.app.schemas import (
    EmotionPredictRequest,
    EmotionPredictResponse,
    KeywordRequest,
    KeywordResponse,
    TrendRequest,
    TrendResponse,
)
from model_service.app.text_utils import extract_keywords


app = FastAPI(title="MoodFlow Model Service", version="0.1.0")
predictor = EmotionPredictor()


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "model_ready": predictor.ready,
        "model_version": predictor.version,
    }


@app.post("/predict/emotion", response_model=EmotionPredictResponse)
def predict_emotion(payload: EmotionPredictRequest) -> dict[str, object]:
    return predictor.predict(payload.text, payload.selected_label)


@app.post("/extract/keywords", response_model=KeywordResponse)
def keywords(payload: KeywordRequest) -> dict[str, object]:
    return {"keywords": extract_keywords(payload.text, payload.top_k)}


@app.post("/analyze/trend", response_model=TrendResponse)
def trend(payload: TrendRequest) -> dict[str, object]:
    return analyze_trend(payload.records)
