from __future__ import annotations

import re
from collections import Counter

import jieba


URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
MENTION_RE = re.compile(r"@\S+")
SPACE_RE = re.compile(r"\s+")
KEEP_RE = re.compile(r"[^\u4e00-\u9fffA-Za-z0-9，。！？；：（）()、《》“”‘’—\-]+")

STOPWORDS = {
    "的",
    "了",
    "是",
    "我",
    "你",
    "他",
    "她",
    "它",
    "我们",
    "你们",
    "他们",
    "一个",
    "一些",
    "有点",
    "真的",
    "就是",
    "这个",
    "那个",
    "因为",
    "所以",
    "但是",
}


def normalize_text(text: str) -> str:
    text = (text or "").strip()
    text = URL_RE.sub(" ", text)
    text = MENTION_RE.sub(" ", text)
    text = KEEP_RE.sub(" ", text)
    text = SPACE_RE.sub(" ", text)
    return text.strip()


def jieba_tokenize(text: str) -> list[str]:
    normalized = normalize_text(text)
    return [
        token.strip()
        for token in jieba.lcut(normalized)
        if token.strip() and token.strip() not in STOPWORDS
    ]


def extract_keywords(text: str, top_k: int = 8) -> list[str]:
    tokens = [token for token in jieba_tokenize(text) if len(token) > 1]
    counter = Counter(tokens)
    return [word for word, _ in counter.most_common(top_k)]
