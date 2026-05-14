# Development Checklist

## 1. 环境准备

- 复制环境变量：`cp .env.example .env`
- 安装后端依赖：`python -m pip install -r backend/requirements.txt`
- 安装模型服务依赖：`python -m pip install -r model_service/requirements.txt`
- 本地不连 MySQL 时保持默认 SQLite；连 MySQL 时设置 `MYSQL_HOST`、`MYSQL_DATABASE`、`MYSQL_USER`、`MYSQL_PASSWORD`

## 2. 迁移

```bash
cd backend
python manage.py migrate
```

Docker 环境：

```bash
make migrate
```

## 3. Seed

当前代码里可用的 seed 命令按模块拆分：

```bash
cd backend
python manage.py seed_admin
python manage.py seed_emotions
python manage.py seed_content
python manage.py seed_tree_holes
python manage.py seed_usage_logs
python manage.py seed_model_versions
```

执行后确认管理员账号、情绪标签、陪伴内容、树洞审核样例都已写入。

## 4. 训练

```bash
PYTHONPATH=. python -m model_service.training.dataset_builder \
  --raw-dir data/raw \
  --output data/processed/moodflow_emotions.csv

PYTHONPATH=. python -m model_service.training.train_baseline \
  --dataset data/processed/moodflow_emotions.csv \
  --output-dir model_service/artifacts/baseline
```

如果走 Makefile 编排，直接执行 `make train-baseline`。

## 5. 启动

一键启动：

```bash
make up
```

本地分别启动：

```bash
cd backend
python manage.py runserver 0.0.0.0:8000
```

```bash
PYTHONPATH=. uvicorn model_service.app.main:app --host 0.0.0.0 --port 8010
```

健康检查：

```bash
curl http://localhost:8000/api/health/
curl http://localhost:8010/health
```

## 6. 测试

依赖完整时运行 pytest：

```bash
cd backend
python -m pytest tests
```

依赖不完整时至少做语法检查：

```bash
python -m compileall backend/tests
```

提交前建议补跑：

```bash
make lint
make healthcheck
```

## 7. 深度学习脚本说明

`model_service/training/train_transformer.py` 可用于后续 GPU 环境微调 `bert-base-chinese` 等模型。当前 FastAPI 推理服务默认加载 `model_service/artifacts/baseline/model.joblib`，不会直接加载 Hugging Face `best/` 目录。
