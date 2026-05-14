from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Iterable

from model_service.app.labels import MOODFLOW_LABELS
from model_service.app.text_utils import normalize_text


SMP_LABEL_MAP = {
    "happy": "happy",
    "angry": "irritable",
    "sad": "sad",
    "fear": "anxious",
    "surprise": "expecting",
    "neutral": "plain",
}

CHINESE_DIALOGUE_LABEL_MAP = {
    "平淡": "plain",
    "开心": "happy",
    "悲伤": "sad",
    "愤怒": "irritable",
    "惊讶": "expecting",
    "恐惧": "anxious",
    "厌恶": "irritable",
    "疑问": "anxious",
    "关切": "anxious",
    "平淡語氣": "plain",
    "開心語調": "happy",
    "悲傷語調": "sad",
    "憤怒語調": "irritable",
    "驚奇語調": "expecting",
    "恐懼語調": "anxious",
    "厭惡語調": "irritable",
    "疑問語調": "anxious",
    "關切語調": "anxious",
}

CPED_LABEL_MAP = {
    "happy": "happy",
    "grateful": "happy",
    "relaxed": "calm",
    "other-positive": "expecting",
    "neutral": "plain",
    "angry": "irritable",
    "sad": "sad",
    "feared": "anxious",
    "depressed": "sad",
    "disgusted": "irritable",
    "astonished": "expecting",
    "worried": "anxious",
    "other-negative": "irritable",
}

SYNTHETIC_SAMPLES = [
    ("今天只是安安静静地过完了，心里很平和。", "calm", "synthetic"),
    ("做完呼吸练习之后感觉整个人都放松下来了。", "calm", "synthetic"),
    ("很期待明天的旅行，想到就有一点兴奋。", "expecting", "synthetic"),
    ("盼了很久的消息终于快要来了，希望一切顺利。", "expecting", "synthetic"),
    ("连续加班之后真的很疲惫，只想好好睡一觉。", "tired", "synthetic"),
    ("今天身体和脑子都很累，完全没有精神。", "tired", "synthetic"),
    ("熬夜之后头很沉，什么都不想做。", "tired", "synthetic"),
    ("事情太多压在一起，心里一直紧张不安。", "anxious", "synthetic"),
    ("一点小事都让我很烦躁，感觉快没有耐心了。", "irritable", "synthetic"),
    ("虽然没什么特别开心的事，但今天很平淡。", "plain", "synthetic"),
]

TIRED_SCENES = [
    "连续加班之后",
    "熬夜复习之后",
    "忙了一整天之后",
    "运动过量之后",
    "通勤很久之后",
    "照顾家人一整晚之后",
    "会议排满之后",
    "周末也没有休息之后",
]

TIRED_FEELINGS = [
    "真的很疲惫，只想安静地躺一会儿。",
    "身体很累，脑子也转不动了。",
    "一点精神都没有，连说话都觉得费劲。",
    "整个人像没电了一样，需要好好睡一觉。",
    "觉得乏力又困倦，什么都不太想做。",
]

CALM_SCENES = [
    "散步回来之后",
    "听完白噪音之后",
    "做完呼吸练习之后",
    "收拾好房间之后",
    "窗外下着小雨的时候",
]

EXPECTING_SCENES = [
    "想到明天的计划",
    "等待重要消息的时候",
    "准备出发旅行前",
    "快要见到朋友的时候",
    "新项目马上开始前",
]


def iter_synthetic_samples() -> Iterable[dict[str, str]]:
    for text, label, source in SYNTHETIC_SAMPLES:
        yield {"text": text, "label": label, "source": source}
    for scene in TIRED_SCENES:
        for feeling in TIRED_FEELINGS:
            yield {"text": f"{scene}{feeling}", "label": "tired", "source": "synthetic_tired"}
    for scene in CALM_SCENES:
        yield {"text": f"{scene}，心里慢慢安静下来，感觉很平和。", "label": "calm", "source": "synthetic_calm"}
    for scene in EXPECTING_SCENES:
        yield {"text": f"{scene}，心里有一点期待，也有一点兴奋。", "label": "expecting", "source": "synthetic_expecting"}


def iter_smp(path: Path, source: str) -> Iterable[dict[str, str]]:
    if not path.exists():
        return
    raw = path.read_text(encoding="utf-8")
    try:
        records = json.loads(raw)
    except json.JSONDecodeError:
        records = [json.loads(line) for line in raw.splitlines() if line.strip()]
    for record in records:
        label = SMP_LABEL_MAP.get(str(record.get("label", "")).strip())
        text = normalize_text(str(record.get("content", "")))
        if label and text:
            yield {"text": text, "label": label, "source": source}


def iter_chinese_dialogue(path: Path) -> Iterable[dict[str, str]]:
    if not path.exists():
        return
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            label = CHINESE_DIALOGUE_LABEL_MAP.get(row.get("emotion", "").strip())
            text = normalize_text(row.get("text", ""))
            if label and text:
                yield {"text": text, "label": label, "source": "chinese_multi_emotion_dialogue"}


def iter_cped(path: Path, source: str) -> Iterable[dict[str, str]]:
    if not path.exists():
        return
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            label = CPED_LABEL_MAP.get(row.get("Emotion", "").strip())
            text = normalize_text(row.get("Utterance", ""))
            if label and text:
                yield {"text": text, "label": label, "source": source}


def build_dataset(raw_dir: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    smp_dir = raw_dir / "smp2020-ewect" / "data" / "clean"
    for name in [
        "usual_train.txt",
        "usual_eval_labeled.txt",
        "usual_test_labeled.txt",
        "virus_train.txt",
        "virus_eval_labeled.txt",
        "virus_test_labeled.txt",
    ]:
        rows.extend(iter_smp(smp_dir / name, f"smp2020_{name}"))

    rows.extend(iter_chinese_dialogue(raw_dir / "chinese_multi_emotion_dialogue.csv"))

    cped_dir = raw_dir / "cped" / "data" / "CPED"
    for name in ["train_split.csv", "valid_split.csv", "test_split.csv"]:
        rows.extend(iter_cped(cped_dir / name, f"cped_{name}"))

    rows.extend(iter_synthetic_samples())

    seen: set[tuple[str, str]] = set()
    deduped: list[dict[str, str]] = []
    for row in rows:
        if row["label"] not in MOODFLOW_LABELS:
            continue
        key = (row["text"], row["label"])
        if key not in seen:
            seen.add(key)
            deduped.append(row)
    return deduped


def write_dataset(rows: list[dict[str, str]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["text", "label", "source"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", default="data/raw")
    parser.add_argument("--output", default="data/processed/moodflow_emotions.csv")
    args = parser.parse_args()

    rows = build_dataset(Path(args.raw_dir))
    write_dataset(rows, Path(args.output))
    counts = {label: 0 for label in MOODFLOW_LABELS}
    for row in rows:
        counts[row["label"]] += 1
    print(json.dumps({"rows": len(rows), "label_counts": counts}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
