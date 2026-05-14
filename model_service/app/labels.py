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

LABEL_DISPLAY = {
    "happy": "今天挺开心",
    "calm": "心里比较稳",
    "expecting": "有点期待",
    "anxious": "有点慌",
    "sad": "心里低落",
    "irritable": "有点炸毛",
    "plain": "没什么波动",
    "tired": "像没电了",
}

LABEL_HINT = {
    "happy": "有值得记住的好事",
    "calm": "节奏刚刚好",
    "expecting": "心里有盼头",
    "anxious": "脑子停不下来",
    "sad": "需要一点缓冲",
    "irritable": "像被很多事同时拉扯",
    "plain": "今天比较普通",
    "tired": "身体和脑子都想歇一会儿",
}

LABEL_RECOMMENDATIONS = {
    "happy": ["template", "article", "phrase"],
    "calm": ["music", "phrase", "article"],
    "expecting": ["template", "article", "phrase"],
    "anxious": ["breathing", "advice", "music"],
    "sad": ["phrase", "template", "music"],
    "irritable": ["breathing", "music", "advice"],
    "plain": ["article", "template", "phrase"],
    "tired": ["music", "phrase", "advice"],
}

POSITIVE_LABELS = {"happy", "calm", "expecting"}
NEGATIVE_LABELS = {"anxious", "sad", "irritable", "tired"}
NEUTRAL_LABELS = {"plain"}


@dataclass(frozen=True)
class LabelInfo:
    code: str
    name: str
    display_name: str
    display_hint: str
    category: str
    recommended_content_types: list[str]


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
        display_name=LABEL_DISPLAY[normalized],
        display_hint=LABEL_HINT[normalized],
        category=label_category(normalized),
        recommended_content_types=LABEL_RECOMMENDATIONS[normalized],
    )
