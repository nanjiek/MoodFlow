from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Optional BERT/RoBERTa fine-tuning entrypoint.")
    parser.add_argument("--dataset", default="data/processed/moodflow_emotions.csv")
    parser.add_argument("--model-name", default="bert-base-chinese")
    parser.add_argument("--output-dir", default="model_service/artifacts/bert")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()

    try:
        import evaluate
        import numpy as np
        import pandas as pd
        from datasets import Dataset
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
    dataset = Dataset.from_pandas(df[["text", "labels"]], preserve_index=False).train_test_split(
        test_size=0.15,
        seed=42,
        stratify_by_column="labels",
    )

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
    training_args = TrainingArguments(
        output_dir=str(output_dir),
        learning_rate=2e-5,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        num_train_epochs=args.epochs,
        weight_decay=0.01,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        report_to=[],
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["test"],
        tokenizer=tokenizer,
        data_collator=DataCollatorWithPadding(tokenizer=tokenizer),
        compute_metrics=compute_metrics,
    )
    trainer.train()
    trainer.save_model(str(output_dir / "best"))
    tokenizer.save_pretrained(str(output_dir / "best"))


if __name__ == "__main__":
    main()
