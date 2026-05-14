from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import joblib

from model_service.app.labels import LABEL_ZH, MOODFLOW_LABELS, label_info
from model_service.app.text_utils import extract_keywords, normalize_text


class PredictorNotReady(RuntimeError):
    """Raised when no trained model artifact is available."""


class EmotionPredictor:
    def __init__(self, model_dir: str | os.PathLike[str] | None = None) -> None:
        self.model_dir = Path(model_dir or os.getenv("MODEL_DIR", "model_service/artifacts/baseline"))
        self.pipeline: Any | None = None
        self.metadata: dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        model_path = self.model_dir / "model.joblib"
        metadata_path = self.model_dir / "metadata.json"
        if model_path.exists():
            self.pipeline = joblib.load(model_path)
        if metadata_path.exists():
            self.metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    @property
    def ready(self) -> bool:
        return self.pipeline is not None

    @property
    def version(self) -> str:
        return str(self.metadata.get("version") or "baseline-untrained")

    def predict(self, text: str, selected_label: str | None = None) -> dict[str, Any]:
        normalized = normalize_text(text)
        if not normalized:
            normalized = text.strip()

        if not self.pipeline:
            return self._rule_based_predict(normalized, selected_label)

        labels = list(getattr(self.pipeline, "classes_", [])) or MOODFLOW_LABELS
        if hasattr(self.pipeline, "predict_proba"):
            proba = self.pipeline.predict_proba([normalized])[0]
            probabilities = {label: float(score) for label, score in zip(labels, proba)}
        else:
            predicted = self.pipeline.predict([normalized])[0]
            probabilities = {label: 0.0 for label in labels}
            probabilities[predicted] = 1.0

        probabilities = self._apply_domain_calibration(normalized, probabilities, selected_label)

        label = max(probabilities, key=probabilities.get)
        confidence = float(probabilities[label])
        return self._format_result(label, confidence, probabilities, normalized)

    def _apply_domain_calibration(
        self,
        text: str,
        probabilities: dict[str, float],
        selected_label: str | None,
    ) -> dict[str, float]:
        calibrated = {label: float(probabilities.get(label, 0.0)) for label in MOODFLOW_LABELS}
        keyword_map = {
            "happy": ["开心", "快乐", "幸福", "满足", "顺利", "喜欢", "哈哈", "成功"],
            "calm": ["平静", "放松", "安宁", "舒服", "淡然", "舒缓"],
            "expecting": ["期待", "盼望", "希望", "想要", "等着", "兴奋", "旅行", "计划"],
            "anxious": ["焦虑", "紧张", "担心", "害怕", "不安", "压力", "迷茫", "恐惧"],
            "sad": ["难过", "伤心", "委屈", "失落", "沮丧", "低落", "想哭"],
            "irritable": ["烦", "生气", "愤怒", "火大", "不爽", "讨厌", "烦躁"],
            "plain": ["普通", "平淡", "没感觉", "一般", "日常"],
            "tired": ["疲惫", "累", "困", "没精神", "乏力", "熬夜", "加班", "睡觉"],
        }
        for label, keywords in keyword_map.items():
            hits = sum(keyword in text for keyword in keywords)
            if hits:
                calibrated[label] += min(0.45, 0.14 * hits)
        if any(keyword in text for keyword in ("期待", "盼望", "等着")):
            calibrated["expecting"] += 0.35
        if any(keyword in text for keyword in ("疲惫", "乏力", "没精神")):
            calibrated["tired"] += 0.35
        if any(keyword in text for keyword in ("焦虑", "紧张", "担心")):
            calibrated["anxious"] += 0.25
        if selected_label in MOODFLOW_LABELS:
            calibrated[selected_label] += 0.18
        total = sum(calibrated.values()) or 1.0
        return {label: value / total for label, value in calibrated.items()}

    def _format_result(
        self,
        label: str,
        confidence: float,
        probabilities: dict[str, float],
        text: str,
    ) -> dict[str, Any]:
        info = label_info(label)
        negative_markers = ["很", "非常", "崩溃", "受不了", "压力", "难受", "烦", "累", "怕"]
        intensity = min(1.0, max(0.25, confidence + 0.05 * sum(marker in text for marker in negative_markers)))
        return {
            "label": info.code,
            "label_name": info.name,
            "category": info.category,
            "confidence": round(confidence, 4),
            "intensity": round(float(intensity), 4),
            "keywords": extract_keywords(text),
            "model_version": self.version,
            "probabilities": {
                label: round(float(probabilities.get(label, 0.0)), 4)
                for label in MOODFLOW_LABELS
            },
        }

    def _rule_based_predict(self, text: str, selected_label: str | None = None) -> dict[str, Any]:
        scores = {label: 0.02 for label in MOODFLOW_LABELS}
        keyword_map = {
            "happy": ["开心", "快乐", "幸福", "满足", "顺利", "喜欢", "哈哈", "成功"],
            "calm": ["平静", "放松", "安宁", "舒服", "淡然", "舒缓"],
            "expecting": ["期待", "盼望", "希望", "想要", "等着", "兴奋"],
            "anxious": ["焦虑", "紧张", "担心", "害怕", "不安", "压力", "迷茫", "恐惧"],
            "sad": ["难过", "伤心", "委屈", "失落", "沮丧", "低落", "想哭"],
            "irritable": ["烦", "生气", "愤怒", "火大", "不爽", "讨厌", "烦躁"],
            "plain": ["普通", "平淡", "没感觉", "一般", "日常"],
            "tired": ["疲惫", "累", "困", "没精神", "乏力", "熬夜"],
        }
        for label, keywords in keyword_map.items():
            scores[label] += sum(keyword in text for keyword in keywords) * 0.28
        if selected_label in scores:
            scores[selected_label] += 0.2
        total = sum(scores.values())
        probabilities = {label: score / total for label, score in scores.items()}
        label = max(probabilities, key=probabilities.get)
        return self._format_result(label, probabilities[label], probabilities, text)


def analyze_trend(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        return {
            "trend": "stable",
            "summary": "暂无足够情绪记录，先从今天的一条记录开始。",
            "dominant_label": None,
            "negative_days": 0,
        }
    labels = [record.get("label") or record.get("predicted_label") for record in records]
    counts = {label: labels.count(label) for label in set(labels) if label}
    dominant = max(counts, key=counts.get) if counts else None
    negative_days = sum(label in {"anxious", "sad", "irritable", "tired"} for label in labels[-7:])
    trend = "negative_rising" if negative_days >= 3 else "stable"
    dominant_name = LABEL_ZH.get(dominant or "", dominant or "未知")
    summary = f"最近记录中出现最多的是{dominant_name}。" if dominant else "最近记录比较分散。"
    if negative_days >= 3:
        summary += " 近 7 条记录里负向情绪偏多，建议优先推送呼吸放松或低刺激陪伴内容。"
    return {
        "trend": trend,
        "summary": summary,
        "dominant_label": dominant,
        "negative_days": negative_days,
    }
