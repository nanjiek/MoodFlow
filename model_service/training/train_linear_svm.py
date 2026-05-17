from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from model_service.app.labels import MOODFLOW_LABELS
from model_service.app.text_utils import normalize_text


def _load_dataset(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.dropna(subset=["text", "label"])
    df["text"] = df["text"].map(normalize_text)
    df = df[df["label"].isin(MOODFLOW_LABELS)]
    df = df[df["text"].str.len() > 0]
    return df


def train(dataset: Path, output_dir: Path, test_dataset: Path | None = None) -> dict[str, object]:
    df = _load_dataset(dataset)
    if test_dataset is not None:
        test_df = _load_dataset(test_dataset)
        x_train, y_train = df["text"], df["label"]
        x_test, y_test = test_df["text"], test_df["label"]
        label_counts = {
            k: int(v)
            for k, v in pd.concat([df["label"], test_df["label"]]).value_counts().to_dict().items()
        }
        dataset_ref = f"{dataset} + {test_dataset}"
    else:
        min_count = df["label"].value_counts().min()
        stratify = df["label"] if min_count >= 2 else None
        x_train, x_test, y_train, y_test = train_test_split(
            df["text"],
            df["label"],
            test_size=0.2,
            random_state=42,
            stratify=stratify,
        )
        label_counts = {k: int(v) for k, v in df["label"].value_counts().to_dict().items()}
        dataset_ref = str(dataset)

    pipeline = Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    analyzer="char",
                    ngram_range=(1, 4),
                    min_df=2,
                    max_features=120000,
                    sublinear_tf=True,
                ),
            ),
            (
                "clf",
                LinearSVC(
                    class_weight="balanced",
                    C=1.0,
                    dual="auto",
                    max_iter=3000,
                ),
            ),
        ]
    )
    pipeline.fit(x_train, y_train)
    y_pred = pipeline.predict(x_test)

    metrics = {
        "version": datetime.now(timezone.utc).strftime("linear-svm-%Y%m%d%H%M%S"),
        "dataset": dataset_ref,
        "train_size": int(len(x_train)),
        "test_size": int(len(x_test)),
        "labels": MOODFLOW_LABELS,
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "macro_f1": float(f1_score(y_test, y_pred, average="macro")),
        "weighted_f1": float(f1_score(y_test, y_pred, average="weighted")),
        "label_counts": label_counts,
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
    parser.add_argument("--test-dataset")
    parser.add_argument("--output-dir", default="model_service/artifacts/linear-svm")
    args = parser.parse_args()
    metrics = train(
        Path(args.dataset),
        Path(args.output_dir),
        Path(args.test_dataset) if args.test_dataset else None,
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
