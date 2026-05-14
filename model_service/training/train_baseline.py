from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from model_service.app.labels import MOODFLOW_LABELS
from model_service.app.text_utils import normalize_text


def train(dataset: Path, output_dir: Path) -> dict[str, object]:
    df = pd.read_csv(dataset)
    df = df.dropna(subset=["text", "label"])
    df["text"] = df["text"].map(normalize_text)
    df = df[df["label"].isin(MOODFLOW_LABELS)]
    df = df[df["text"].str.len() > 0]

    min_count = df["label"].value_counts().min()
    stratify = df["label"] if min_count >= 2 else None
    x_train, x_test, y_train, y_test = train_test_split(
        df["text"],
        df["label"],
        test_size=0.2,
        random_state=42,
        stratify=stratify,
    )

    pipeline = Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    analyzer="char",
                    ngram_range=(1, 3),
                    min_df=2,
                    max_features=80000,
                    sublinear_tf=True,
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    max_iter=1200,
                    class_weight="balanced",
                    solver="lbfgs",
                    n_jobs=-1,
                ),
            ),
        ]
    )
    pipeline.fit(x_train, y_train)
    y_pred = pipeline.predict(x_test)

    metrics = {
        "version": datetime.now(timezone.utc).strftime("baseline-%Y%m%d%H%M%S"),
        "dataset": str(dataset),
        "train_size": int(len(x_train)),
        "test_size": int(len(x_test)),
        "labels": MOODFLOW_LABELS,
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "macro_f1": float(f1_score(y_test, y_pred, average="macro")),
        "weighted_f1": float(f1_score(y_test, y_pred, average="weighted")),
        "label_counts": {k: int(v) for k, v in df["label"].value_counts().to_dict().items()},
        "classification_report": classification_report(
            y_test,
            y_pred,
            labels=MOODFLOW_LABELS,
            output_dict=True,
            zero_division=0,
        ),
        "confusion_matrix": confusion_matrix(y_test, y_pred, labels=MOODFLOW_LABELS).tolist(),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, output_dir / "model.joblib")
    (output_dir / "metadata.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="data/processed/moodflow_emotions.csv")
    parser.add_argument("--output-dir", default="model_service/artifacts/baseline")
    args = parser.parse_args()
    metrics = train(Path(args.dataset), Path(args.output_dir))
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
