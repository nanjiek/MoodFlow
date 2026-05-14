from __future__ import annotations

import csv
import json

import pytest


pytest.importorskip("joblib")
pytest.importorskip("jieba")
pytest.importorskip("model_service")

from model_service.training.dataset_builder import build_dataset, write_dataset


def test_predictor_uses_rule_based_fallback_when_model_is_missing(tmp_path) -> None:
    from model_service.app.predictor import EmotionPredictor

    predictor = EmotionPredictor(model_dir=tmp_path)

    result = predictor.predict("最近压力很大，心里一直很焦虑，也很担心明天的汇报")

    assert predictor.ready is False
    assert result["label"] == "anxious"
    assert result["label_name"] == "焦虑"
    assert result["display_name"] == "有点慌"
    assert result["category"] == "negative"
    assert result["model_version"] == "baseline-untrained"
    assert result["confidence"] > result["probabilities"]["plain"]
    assert "有点慌" in result["explanation"]
    assert result["recommended_content_types"][0] == "breathing"
    assert sum(result["probabilities"].values()) == pytest.approx(1.0, abs=0.01)


def test_build_dataset_with_small_raw_samples(tmp_path) -> None:
    raw_dir = tmp_path / "raw"

    smp_dir = raw_dir / "smp2020-ewect" / "data" / "clean"
    smp_dir.mkdir(parents=True)
    (smp_dir / "usual_train.txt").write_text(
        json.dumps(
            [
                {"content": "今天很开心", "label": "happy"},
                {"content": "我有点害怕", "label": "fear"},
                {"content": "这个标签会被过滤", "label": "unknown"},
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    chinese_dialogue_path = raw_dir / "chinese_multi_emotion_dialogue.csv"
    chinese_dialogue_path.parent.mkdir(parents=True, exist_ok=True)
    with chinese_dialogue_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["text", "emotion"])
        writer.writeheader()
        writer.writerow({"text": "明天要展示，心里有点紧张", "emotion": "恐惧"})

    cped_dir = raw_dir / "cped" / "data" / "CPED"
    cped_dir.mkdir(parents=True)
    with (cped_dir / "train_split.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["Utterance", "Emotion"])
        writer.writeheader()
        writer.writerow({"Utterance": "做完练习之后很放松", "Emotion": "relaxed"})
        writer.writerow({"Utterance": "今天很开心", "Emotion": "happy"})

    rows = build_dataset(raw_dir)
    labels_by_text = {row["text"]: row["label"] for row in rows}

    assert labels_by_text["今天很开心"] == "happy"
    assert labels_by_text["我有点害怕"] == "anxious"
    assert labels_by_text["明天要展示，心里有点紧张"] == "anxious"
    assert labels_by_text["做完练习之后很放松"] == "calm"
    assert "这个标签会被过滤" not in labels_by_text
    assert sum(row["text"] == "今天很开心" and row["label"] == "happy" for row in rows) == 1
    assert any(row["source"] == "synthetic" for row in rows)

    output_path = tmp_path / "processed" / "moodflow_emotions.csv"
    write_dataset(rows, output_path)

    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8").startswith("text,label,source")
