# MoodFlow Model Service

This service provides the emotion classification layer for MoodFlow. It supports:

- dataset normalization from downloaded raw datasets;
- a lightweight TF-IDF + Logistic Regression baseline;
- a FastAPI inference API;
- an optional BERT fine-tuning script for later GPU runs.

## Prepare Dataset

```bash
python -m model_service.training.dataset_builder \
  --raw-dir data/raw \
  --output data/processed/moodflow_emotions.csv
```

## Train Baseline

```bash
python -m model_service.training.train_baseline \
  --dataset data/processed/moodflow_emotions.csv \
  --output-dir model_service/artifacts/baseline
```

## Run API

```bash
uvicorn model_service.app.main:app --host 0.0.0.0 --port 8010
```

The running service loads the lightweight baseline artifact at `model_service/artifacts/baseline/model.joblib`.
`training/train_transformer.py` is included for optional GPU fine-tuning experiments; its Hugging Face output is not loaded by the FastAPI service unless a serving adapter is added later.

## Predict

```bash
curl -X POST http://localhost:8010/predict/emotion \
  -H 'Content-Type: application/json' \
  -d '{"text":"今天压力很大，心里一直很紧张"}'
```
