from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Optional BERT/RoBERTa fine-tuning entrypoint.")
    parser.add_argument("--dataset", default="data/processed/moodflow_emotions.csv")
    parser.add_argument("--test-dataset")
    parser.add_argument("--model-name", default="hfl/rbt3")
    parser.add_argument("--output-dir", default="model_service/artifacts/transformer-rbt3")
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--max-train-samples", type=int, default=24000)
    parser.add_argument("--max-eval-samples", type=int, default=4000)
    args = parser.parse_args()

    try:
        import evaluate
        import numpy as np
        import pandas as pd
        from datasets import Dataset, DatasetDict
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
        from transformers import (
            AutoModelForSequenceClassification,
            AutoTokenizer,
            DataCollatorWithPadding,
            Trainer,
            TrainingArguments,
        )
    except ImportError as exc:
        raise SystemExit(
            "Transformer training dependencies are not installed. "
            "Run: pip install -r model_service/requirements-bert.txt"
        ) from exc

    from model_service.app.labels import MOODFLOW_LABELS
    from model_service.app.text_utils import normalize_text

    df = pd.read_csv(args.dataset).dropna(subset=["text", "label"])
    df = df[df["label"].isin(MOODFLOW_LABELS)]
    df["text"] = df["text"].map(normalize_text)
    label_to_id = {label: idx for idx, label in enumerate(MOODFLOW_LABELS)}
    id_to_label = {idx: label for label, idx in label_to_id.items()}
    df["labels"] = df["label"].map(label_to_id)
    if args.test_dataset:
        test_df_full = pd.read_csv(args.test_dataset).dropna(subset=["text", "label"])
        test_df_full = test_df_full[test_df_full["label"].isin(MOODFLOW_LABELS)]
        test_df_full["text"] = test_df_full["text"].map(normalize_text)
        test_df_full["labels"] = test_df_full["label"].map(label_to_id)
        train_df = df[["text", "labels"]]
        test_df = test_df_full[["text", "labels"]]
        dataset_ref = f"{args.dataset} + {args.test_dataset}"
        label_counts = {
            k: int(v)
            for k, v in pd.concat([df["label"], test_df_full["label"]]).value_counts().to_dict().items()
        }
    else:
        train_df, test_df = train_test_split(
            df[["text", "labels"]],
            test_size=0.15,
            random_state=42,
            stratify=df["labels"],
        )
        dataset_ref = str(args.dataset)
        label_counts = {k: int(v) for k, v in df["label"].value_counts().to_dict().items()}
    dataset = DatasetDict(
        {
            "train": Dataset.from_pandas(train_df.reset_index(drop=True), preserve_index=False),
            "test": Dataset.from_pandas(test_df.reset_index(drop=True), preserve_index=False),
        }
    )
    if args.max_train_samples and len(dataset["train"]) > args.max_train_samples:
        dataset["train"] = dataset["train"].shuffle(seed=42).select(range(args.max_train_samples))
    if args.max_eval_samples and len(dataset["test"]) > args.max_eval_samples:
        dataset["test"] = dataset["test"].shuffle(seed=42).select(range(args.max_eval_samples))

    tokenizer = AutoTokenizer.from_pretrained(args.model_name)

    def tokenize(batch):
        return tokenizer(batch["text"], truncation=True, max_length=160)

    tokenized = dataset.map(tokenize, batched=True)
    metric = evaluate.load("f1")

    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        predictions = np.argmax(logits, axis=-1)
        return {
            "macro_f1": metric.compute(predictions=predictions, references=labels, average="macro")["f1"],
        }

    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_name,
        num_labels=len(MOODFLOW_LABELS),
        id2label=id_to_label,
        label2id=label_to_id,
    )
    output_dir = Path(args.output_dir)
    checkpoints_dir = output_dir / "checkpoints"
    training_args = TrainingArguments(
        output_dir=str(checkpoints_dir),
        learning_rate=2e-5,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        num_train_epochs=args.epochs,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        report_to=[],
        logging_strategy="steps",
        logging_steps=50,
        save_total_limit=2,
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["test"],
        data_collator=DataCollatorWithPadding(tokenizer=tokenizer),
        compute_metrics=compute_metrics,
    )
    train_result = trainer.train()

    output_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))

    eval_prediction = trainer.predict(tokenized["test"])
    predicted_ids = np.argmax(eval_prediction.predictions, axis=-1)
    true_ids = np.array(eval_prediction.label_ids)
    labels = list(range(len(MOODFLOW_LABELS)))
    predicted_labels = [id_to_label[int(item)] for item in predicted_ids]
    true_labels = [id_to_label[int(item)] for item in true_ids]

    metrics = {
        "version": datetime.now(timezone.utc).strftime("transformer-%Y%m%d%H%M%S"),
        "base_model": args.model_name,
        "dataset": dataset_ref,
        "train_size": int(len(dataset["train"])),
        "test_size": int(len(dataset["test"])),
        "labels": MOODFLOW_LABELS,
        "accuracy": float(accuracy_score(true_labels, predicted_labels)),
        "macro_f1": float(f1_score(true_labels, predicted_labels, average="macro")),
        "weighted_f1": float(f1_score(true_labels, predicted_labels, average="weighted")),
        "label_counts": label_counts,
        "classification_report": classification_report(
            true_labels,
            predicted_labels,
            labels=MOODFLOW_LABELS,
            output_dict=True,
            zero_division=0,
        ),
        "confusion_matrix": confusion_matrix(true_labels, predicted_labels, labels=MOODFLOW_LABELS).tolist(),
        "train_runtime_seconds": float(train_result.metrics.get("train_runtime", 0.0)),
        "train_samples_per_second": float(train_result.metrics.get("train_samples_per_second", 0.0)),
    }
    (output_dir / "metadata.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
