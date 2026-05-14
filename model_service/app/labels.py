from __future__ import annotations

from dataclasses import dataclass


MOODFLOW_LABELS = [
    "happy",
    "calm",
    "expecting",
    "anxious",
    "sad",
    "irritable",
    "plain",
    "tired",
]

LABEL_ZH = {
    "happy": "开心",
    "calm": "平静",
    "expecting": "期待",
    "anxious": "焦虑",
    "sad": "难过",
    "irritable": "烦躁",
    "plain": "平淡",
    "tired": "疲惫",
}

POSITIVE_LABELS = {"happy", "calm", "expecting"}
NEGATIVE_LABELS = {"anxious", "sad", "irritable", "tired"}
NEUTRAL_LABELS = {"plain"}


@dataclass(frozen=True)
class LabelInfo:
    code: str
    name: str
    category: str


def label_category(label: str) -> str:
    if label in POSITIVE_LABELS:
        return "positive"
    if label in NEGATIVE_LABELS:
        return "negative"
    return "neutral"


def label_info(label: str) -> LabelInfo:
    normalized = label if label in LABEL_ZH else "plain"
    return LabelInfo(
        code=normalized,
        name=LABEL_ZH[normalized],
        category=label_category(normalized),
    )
