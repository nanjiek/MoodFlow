# MoodFlow Model Service

This service provides the emotion classification layer for MoodFlow. It supports:

- dataset normalization from downloaded raw datasets;
- a lightweight TF-IDF + Logistic Regression baseline;
- a FastAPI inference API;
- an optional BERT/RoBERTa fine-tuning script and local artifact loading.

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
  --output-dir model_service/artifacts/baseline-clean-v4
```

## Run API

```bash
uvicorn model_service.app.main:app --host 0.0.0.0 --port 8010
```

The running service loads the artifact referenced by `MODEL_DIR`. The current default is `baseline-clean-v4`.

- `model_service/artifacts/baseline-clean-v4` contains the retained TF-IDF + Logistic Regression baseline (`model.joblib`).
- Older experiment artifacts are archived under `model_service/artifacts/experiments/`.
- Transformer artifacts saved by `training/train_transformer.py` can now also be loaded directly when `MODEL_DIR` points to a Hugging Face sequence-classification directory containing `config.json` and model weights.

Example local transformer training:

```bash
python -m model_service.training.train_transformer \
  --dataset data/processed/moodflow_emotions.csv \
  --model-name hfl/rbt3 \
  --output-dir model_service/artifacts/experiments/transformer-rbt3-local
```

## Predict

```bash
curl -X POST http://localhost:8010/predict/emotion \
  -H 'Content-Type: application/json' \
  -d '{"text":"今天压力很大，心里一直很紧张"}'
```
