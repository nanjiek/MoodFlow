from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import joblib

from model_service.app.labels import LABEL_ZH, MOODFLOW_LABELS, label_info
from model_service.app.text_utils import extract_keywords, normalize_text


KEYWORD_MAP = {
    "happy": ["开心", "快乐", "幸福", "满足", "顺利", "喜欢", "哈哈", "成功"],
    "calm": ["平静", "放松", "安宁", "舒服", "淡然", "舒缓"],
    "expecting": ["期待", "盼望", "希望", "想要", "等着", "兴奋", "旅行", "计划"],
    "anxious": ["焦虑", "紧张", "担心", "害怕", "不安", "压力", "迷茫", "恐惧"],
    "sad": ["难过", "伤心", "委屈", "失落", "沮丧", "低落", "想哭"],
    "irritable": ["烦", "生气", "恼火", "火大", "不爽", "讨厌", "烦躁"],
    "plain": ["普通", "平淡", "没感觉", "一般", "日常"],
    "tired": ["疲惫", "累", "困", "没精神", "乏力", "熬夜", "加班", "睡觉"],
}

NEGATIVE_MARKERS = ["很", "非常", "崩溃", "受不了", "压力", "难受", "烦", "累", "慌"]


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
        for label, keywords in KEYWORD_MAP.items():
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
        intensity = min(1.0, max(0.25, confidence + 0.05 * sum(marker in text for marker in NEGATIVE_MARKERS)))
        keywords = extract_keywords(text)
        return {
            "label": info.code,
            "label_name": info.name,
            "display_name": info.display_name,
            "display_hint": info.display_hint,
            "category": info.category,
            "confidence": round(confidence, 4),
            "intensity": round(float(intensity), 4),
            "keywords": keywords,
            "explanation": self._build_explanation(info.display_name, keywords),
            "gentle_feedback": self._build_gentle_feedback(info.code),
            "recommended_content_types": info.recommended_content_types,
            "suggested_prompt": self._suggested_prompt(info.code),
            "model_version": self.version,
            "probabilities": {
                current_label: round(float(probabilities.get(current_label, 0.0)), 4)
                for current_label in MOODFLOW_LABELS
            },
        }

    def _rule_based_predict(self, text: str, selected_label: str | None = None) -> dict[str, Any]:
        scores = {label: 0.02 for label in MOODFLOW_LABELS}
        for label, keywords in KEYWORD_MAP.items():
            scores[label] += sum(keyword in text for keyword in keywords) * 0.28
        if selected_label in scores:
            scores[selected_label] += 0.2
        total = sum(scores.values())
        probabilities = {label: score / total for label, score in scores.items()}
        label = max(probabilities, key=probabilities.get)
        return self._format_result(label, probabilities[label], probabilities, text)

    def _build_explanation(self, display_name: str, keywords: list[str]) -> str:
        if keywords:
            top_keywords = "、".join(keywords[:3])
            return f"你提到了“{top_keywords}”，整体表达更接近“{display_name}”这类状态。"
        return f"这次没有抓到特别强的关键词，但整体语气更接近“{display_name}”。"

    def _build_gentle_feedback(self, label: str) -> str:
        if label == "anxious":
            return "先别急着把所有问题一次想完，能看清下一步，就已经很不容易了。"
        if label == "sad":
            return "难过不需要马上被解决，先让自己被理解，比立刻打起精神更重要。"
        if label == "irritable":
            return "烦躁很多时候是在提醒你已经太满了，先停一停也算进展。"
        if label == "tired":
            return "如果你已经撑了很久，休息不是退步，而是在给自己续航。"
        if label == "happy":
            return "这份开心很值得留下来，它会成为之后回看时很真实的支点。"
        if label == "expecting":
            return "期待本身就是能量，记下你最盼望发生的部分，会更有方向感。"
        if label == "calm":
            return "这种稳定很珍贵，记住是什么让你慢下来，之后还可能帮到你。"
        return "今天的状态也算一种线索，先记下来，慢一点看也没关系。"

    def _suggested_prompt(self, label: str) -> str:
        prompts = {
            "happy": "今天最值得记住的一件好事是什么？",
            "calm": "是什么让你今天慢下来了一点？",
            "expecting": "你现在最期待发生的事是什么？",
            "anxious": "现在最让你挂心的一件事是什么？",
            "sad": "哪一个瞬间让你最有低落感？",
            "irritable": "今天最消耗你的那件事是什么？",
            "plain": "今天虽然普通，但有没有一个小片段值得留下？",
            "tired": "你最明显的累，是身体上的还是脑子里的？",
        }
        return prompts.get(label, "如果只用一句话描述现在，你会怎么说？")


def analyze_trend(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        return {
            "trend": "stable",
            "summary": "暂时还没有足够记录，先从今天的一条情绪开始就很好。",
            "dominant_label": None,
            "negative_days": 0,
            "highlights": [],
            "next_suggestion": "先试试用一句话记录今天最明显的感觉。",
        }

    labels = [record.get("label") or record.get("predicted_label") for record in records]
    counts = {label: labels.count(label) for label in set(labels) if label}
    dominant = max(counts, key=counts.get) if counts else None
    negative_days = sum(label in {"anxious", "sad", "irritable", "tired"} for label in labels[-7:])
    trend = "negative_rising" if negative_days >= 3 else "stable"
    dominant_name = LABEL_ZH.get(dominant or "", dominant or "未知")

    summary = f"最近的记录里，“{dominant_name}”出现得最多。" if dominant else "最近的记录还比较分散。"
    highlights = []
    if dominant:
        highlights.append(f"当前最常见的情绪是“{dominant_name}”。")
    if negative_days >= 3:
        highlights.append("最近 7 条记录里，负面情绪偏多。")
        summary += " 最近 7 条记录里负面情绪偏多，建议优先安排恢复感更强的陪伴内容。"

    next_suggestion = (
        "下次记录时，可以顺手写下当时最明显的触发点和你最需要的支持。"
        if negative_days >= 3
        else "可以继续保持轻量记录，重点记下让状态变好的小线索。"
    )

    return {
        "trend": trend,
        "summary": summary,
        "dominant_label": dominant,
        "negative_days": negative_days,
        "highlights": highlights,
        "next_suggestion": next_suggestion,
    }
