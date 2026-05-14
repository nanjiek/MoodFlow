FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY . /app/model_service

ENV MODEL_DIR=/app/model_service/artifacts/baseline \
    PYTHONPATH=/app

EXPOSE 8010
CMD ["uvicorn", "model_service.app.main:app", "--host", "0.0.0.0", "--port", "8010"]
