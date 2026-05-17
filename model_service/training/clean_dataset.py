from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from sklearn.model_selection import train_test_split


MOODFLOW_LABELS = ("happy", "calm", "expecting", "anxious", "sad", "irritable", "plain", "tired")

LABEL_KEYWORDS = {
    "happy": {"开心", "快乐", "高兴", "幸福", "激动", "惊喜", "喜悦", "满足", "顺利", "好消息"},
    "calm": {"平静", "放松", "安心", "安宁", "舒缓", "淡然", "心安"},
    "expecting": {"期待", "盼望", "盼着", "希望", "等着", "终于", "旅行", "明天见"},
    "anxious": {"焦虑", "紧张", "担心", "害怕", "不安", "恐惧", "忐忑", "心慌", "发慌"},
    "sad": {"难过", "伤心", "失落", "沮丧", "低落", "想哭", "泪目", "悲伤", "委屈"},
    "irritable": {"烦躁", "生气", "恼火", "火大", "不爽", "讨厌", "发飙", "气死", "爆粗口"},
    "plain": {"普通", "平淡", "一般", "日常", "就这样", "还行"},
    "tired": {"疲惫", "累", "困", "没精神", "乏力", "熬夜", "加班", "想睡", "睡觉", "发烧", "头疼", "生病", "难受"},
}

RISKY_CONTEXT_KEYWORDS = {"明天", "放假", "假期", "休息", "旅行", "计划", "期待"}
NEGATIVE_LABELS = {"anxious", "sad", "irritable", "tired"}
POSITIVE_LABELS = {"happy", "calm", "expecting"}
EMOTION_BEARING = set().union(*LABEL_KEYWORDS.values())

GENERIC_SHORT_RE = re.compile(r"^[\u4e00-\u9fffA-Za-z0-9！？?!,.，。、《》“”‘’\-\s]{1,6}$")


@dataclass
class RowAssessment:
    keep: bool
    reasons: list[str]
    matched_labels: list[str]


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def matched_keyword_labels(text: str) -> list[str]:
    matched: list[str] = []
    for label, keywords in LABEL_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            matched.append(label)
    return matched


def has_negated_emotion_phrase(text: str) -> bool:
    for keyword in EMOTION_BEARING:
        for prefix in ("不", "没", "没有", "别", "并不", "不是", "不要", "甭"):
            if f"{prefix}{keyword}" in text:
                return True
    return False


def build_ambiguous_short_texts(rows: list[dict[str, str]]) -> dict[str, set[str]]:
    texts: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        text = (row["text"] or "").strip()
        if 0 < len(text) <= 6:
            texts[text].add(row["label"])
    return {text: labels for text, labels in texts.items() if len(labels) >= 3}


def assess_row(row: dict[str, str], ambiguous_short_texts: dict[str, set[str]]) -> RowAssessment:
    text = (row["text"] or "").strip()
    label = row["label"]
    matched_labels = matched_keyword_labels(text)
    reasons: list[str] = []
    keep = True

    if not text:
        return RowAssessment(False, ["empty_text"], matched_labels)

    if len(text) <= 4 and text in ambiguous_short_texts:
        keep = False
        reasons.append("ambiguous_short_text")

    if len(text) <= 4 and not matched_labels and GENERIC_SHORT_RE.match(text):
        keep = False
        reasons.append("generic_short_text")

    if len(text) <= 2:
        keep = False
        reasons.append("ultra_short_text")

    if matched_labels:
        matched_set = set(matched_labels)
        if matched_set <= NEGATIVE_LABELS and label in POSITIVE_LABELS:
            reasons.append("negative_keyword_vs_positive_label")
            if len(text) <= 8 and not has_negated_emotion_phrase(text):
                keep = False
        elif matched_set <= POSITIVE_LABELS and label in NEGATIVE_LABELS:
            reasons.append("positive_keyword_vs_negative_label")
            if len(text) <= 8 and not has_negated_emotion_phrase(text):
                keep = False
        elif label not in matched_set and len(matched_set) == 1 and label == "plain":
            reasons.append("plain_label_with_strong_emotion_keyword")
        elif len(matched_set) >= 2:
            reasons.append("mixed_emotion_keywords")

    if any(keyword in text for keyword in RISKY_CONTEXT_KEYWORDS):
        reasons.append("risky_context_keyword")

    return RowAssessment(keep, sorted(set(reasons)), matched_labels)


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def stratified_split(clean_rows: list[dict[str, str]], train_path: Path, test_path: Path, test_size: float) -> dict[str, int]:
    labels = [row["label"] for row in clean_rows]
    train_rows, test_rows = train_test_split(
        clean_rows,
        test_size=test_size,
        random_state=42,
        stratify=labels,
    )
    write_rows(train_path, train_rows)
    write_rows(test_path, test_rows)
    return {"train_size": len(train_rows), "test_size": len(test_rows)}


def build_llm_eval_sample(test_rows: list[dict[str, str]], output_path: Path, per_label: int) -> int:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in test_rows:
        grouped[row["label"]].append(row)
    sample_rows: list[dict[str, str]] = []
    for label in MOODFLOW_LABELS:
        sample_rows.extend(grouped[label][:per_label])
    write_rows(output_path, sample_rows)
    return len(sample_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean processed emotion dataset and produce train/test/eval splits.")
    parser.add_argument("--input", default="data/processed/moodflow_emotions.csv")
    parser.add_argument("--output-dir", default="data/processed/clean_v1")
    parser.add_argument("--test-size", type=float, default=0.15)
    parser.add_argument("--llm-eval-per-label", type=int, default=10)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    rows = load_rows(input_path)
    ambiguous_short_texts = build_ambiguous_short_texts(rows)

    cleaned_rows: list[dict[str, str]] = []
    flagged_rows: list[dict[str, str]] = []
    dropped_rows: list[dict[str, str]] = []
    reason_counts = Counter()

    for row in rows:
        assessment = assess_row(row, ambiguous_short_texts)
        enriched = dict(row)
        enriched["matched_labels"] = "|".join(assessment.matched_labels)
        enriched["flags"] = "|".join(assessment.reasons)
        if assessment.keep:
            cleaned_rows.append(dict(row))
            if assessment.reasons:
                flagged_rows.append(enriched)
        else:
            dropped_rows.append(enriched)
        for reason in assessment.reasons:
            reason_counts[reason] += 1

    cleaned_path = output_dir / "moodflow_emotions_cleaned_v1.csv"
    flagged_path = output_dir / "moodflow_emotions_flagged_v1.csv"
    dropped_path = output_dir / "moodflow_emotions_dropped_v1.csv"
    train_path = output_dir / "moodflow_emotions_cleaned_v1_train.csv"
    test_path = output_dir / "moodflow_emotions_cleaned_v1_test.csv"
    llm_eval_path = output_dir / "moodflow_emotions_cleaned_v1_llm_eval.csv"

    write_rows(cleaned_path, cleaned_rows)
    write_rows(flagged_path, flagged_rows)
    write_rows(dropped_path, dropped_rows)

    split_stats = stratified_split(cleaned_rows, train_path, test_path, args.test_size)
    test_rows = load_rows(test_path)
    llm_eval_size = build_llm_eval_sample(test_rows, llm_eval_path, args.llm_eval_per_label)

    report = {
        "input_rows": len(rows),
        "cleaned_rows": len(cleaned_rows),
        "flagged_rows": len(flagged_rows),
        "dropped_rows": len(dropped_rows),
        "reason_counts": dict(reason_counts),
        "ambiguous_short_text_count": len(ambiguous_short_texts),
        "split": split_stats,
        "llm_eval_rows": llm_eval_size,
        "paths": {
            "cleaned": str(cleaned_path),
            "flagged": str(flagged_path),
            "dropped": str(dropped_path),
            "train": str(train_path),
            "test": str(test_path),
            "llm_eval": str(llm_eval_path),
        },
    }
    (output_dir / "cleaning_report_v1.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
