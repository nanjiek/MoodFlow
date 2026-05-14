from __future__ import annotations

from collections import Counter
from typing import Iterable


EMOTION_PRESENTATION = {
    "happy": {
        "name": "开心",
        "display_name": "今天挺开心",
        "display_hint": "有值得记住的好事",
        "energy": "high",
        "valence": "positive",
        "companion_focus": ["phrase", "template", "article"],
    },
    "calm": {
        "name": "平静",
        "display_name": "心里比较稳",
        "display_hint": "节奏刚刚好",
        "energy": "low",
        "valence": "positive",
        "companion_focus": ["music", "phrase", "article"],
    },
    "expecting": {
        "name": "期待",
        "display_name": "有点期待",
        "display_hint": "心里有盼头",
        "energy": "medium",
        "valence": "positive",
        "companion_focus": ["template", "article", "phrase"],
    },
    "anxious": {
        "name": "焦虑",
        "display_name": "有点慌",
        "display_hint": "脑子停不下来",
        "energy": "high",
        "valence": "negative",
        "companion_focus": ["breathing", "advice", "music"],
    },
    "sad": {
        "name": "难过",
        "display_name": "心里低落",
        "display_hint": "需要一点缓冲",
        "energy": "low",
        "valence": "negative",
        "companion_focus": ["phrase", "template", "music"],
    },
    "irritable": {
        "name": "烦躁",
        "display_name": "有点炸毛",
        "display_hint": "像被很多事同时拉扯",
        "energy": "high",
        "valence": "negative",
        "companion_focus": ["breathing", "music", "advice"],
    },
    "plain": {
        "name": "平淡",
        "display_name": "没什么波动",
        "display_hint": "今天比较普通",
        "energy": "medium",
        "valence": "neutral",
        "companion_focus": ["article", "template", "phrase"],
    },
    "tired": {
        "name": "疲惫",
        "display_name": "像没电了",
        "display_hint": "身体和脑子都想歇一会儿",
        "energy": "low",
        "valence": "negative",
        "companion_focus": ["music", "phrase", "advice"],
    },
}

EMOTION_GROWTH_SCORES = {
    "happy": 88,
    "calm": 76,
    "expecting": 72,
    "plain": 60,
    "tired": 42,
    "anxious": 34,
    "sad": 28,
    "irritable": 30,
}

DEFAULT_GUIDED_PROMPTS = [
    "今天让你印象最深的一件事是什么？",
    "如果只用一句话描述现在，你会怎么说？",
    "身体最明显的感觉是什么，比如紧、累、松一口气？",
]

PRIVACY_NOTICES = [
    "情绪记录默认仅自己可见。",
    "你可以开启加密记录，给敏感内容多一层保护。",
    "历史记录支持删除，保留节奏由你决定。",
]


def emotion_presentation(label: str) -> dict[str, object]:
    fallback = EMOTION_PRESENTATION["plain"]
    data = EMOTION_PRESENTATION.get(label, fallback)
    return {"code": label or "plain", **data}


def build_analysis_explanation(label: str, keywords: Iterable[str], cause: str = "") -> str:
    items = [keyword for keyword in keywords if keyword][:3]
    presentation = emotion_presentation(label)
    if cause:
        return cause.strip()
    if items:
        return f"这次判断主要参考了你提到的“{'、'.join(items)}”，整体更像“{presentation['display_name']}”的状态。"
    return f"这次没有抓到特别强的关键词，但整体语气和表达更接近“{presentation['display_name']}”。"


def build_gentle_feedback(label: str, intensity: int | float = 0) -> str:
    if label == "anxious":
        return "先别急着把所有事一次想完，能把下一步缩小一点点，通常就已经是在照顾自己。"
    if label == "sad":
        return "低落的时候不需要立刻振作，先把感受放在这里，也是一种很重要的整理。"
    if label == "irritable":
        return "烦躁往往是在提醒你已经被占满了，先停一停，比硬扛更有用。"
    if label == "tired":
        return "如果你已经撑了很久，休息不是偷懒，而是在给自己重新充电。"
    if label == "happy":
        return "这份开心很值得记下来，之后回看时，它会是很真实的支点。"
    if label == "expecting":
        return "有期待本身就是一种能量，不妨顺手记下你最想发生的那一部分。"
    if label == "calm":
        return "这种稳定很珍贵，记住是什么让你慢下来，之后可能还用得上。"
    if intensity and float(intensity) >= 7:
        return "今天的波动不算小，先把它说清楚，比急着定义自己更重要。"
    return "今天的状态也算一种线索，先记下来，慢一点看也没关系。"


def quick_entry_guide() -> dict[str, object]:
    return {
        "title": "记录今天情绪",
        "target_duration_seconds": 30,
        "text_optional": True,
        "emoji_optional": True,
        "guided_prompts": DEFAULT_GUIDED_PROMPTS,
        "privacy_notices": PRIVACY_NOTICES,
        "encouragement": "哪怕只选一个情绪，也算完成今天的记录。",
    }


def build_weekly_summary(records: Iterable[dict[str, object]]) -> dict[str, object]:
    normalized_records = list(records)
    if not normalized_records:
        return {
            "summary": "这周还没有足够的记录，先从一条简短情绪开始也很好。",
            "dominant_emotion": None,
            "highlights": [],
            "next_suggestion": "先试试用一句话记录今天最明显的感觉。",
        }

    labels = [record.get("label") for record in normalized_records if record.get("label")]
    keywords = []
    for record in normalized_records:
        keywords.extend(record.get("keywords") or [])

    label_counts = Counter(labels)
    dominant_label, dominant_count = label_counts.most_common(1)[0]
    dominant = emotion_presentation(dominant_label)
    keyword_counts = Counter(keyword for keyword in keywords if keyword)

    highlights = [
        f"这周最常出现的是“{dominant['display_name']}”，共 {dominant_count} 次。",
    ]
    if keyword_counts:
        top_keywords = "、".join(item for item, _ in keyword_counts.most_common(3))
        highlights.append(f"你常提到的关键词是 {top_keywords}。")

    negative_count = sum(label in {"anxious", "sad", "irritable", "tired"} for label in labels)
    if negative_count >= 3:
        highlights.append("这一周负面波动偏多，下一周更适合优先安排恢复感和留白。")

    next_suggestion = {
        "anxious": "下次记录时可以顺手写下“现在最担心的一件事”和“能做的最小一步”。",
        "sad": "下次可以试试把让你低落的瞬间和一个想被安慰的点写出来。",
        "irritable": "如果再次烦躁，先标记最耗能的那件事，能帮助你更快看清来源。",
        "tired": "如果最近总是累，建议把记录时间和疲惫出现的场景一起留下来。",
    }.get(dominant_label, "可以继续保持轻量记录，重点记下让状态变好的小线索。")

    return {
        "summary": f"这周整体更偏向“{dominant['display_name']}”，情绪走势已经有一些可观察的模式。",
        "dominant_emotion": dominant,
        "highlights": highlights,
        "next_suggestion": next_suggestion,
    }


def emotion_growth_score(label: str, intensity: int | float = 0) -> int:
    presentation = emotion_presentation(label)
    score = EMOTION_GROWTH_SCORES.get(label, EMOTION_GROWTH_SCORES["plain"])
    intensity_value = max(0, min(int(float(intensity or 0)), 10))

    if presentation["valence"] == "positive":
        score += intensity_value
    elif presentation["valence"] == "negative":
        score -= intensity_value

    return max(0, min(int(score), 100))
