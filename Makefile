COMPOSE ?= docker compose
PYTHON ?= python3

BACKEND_RUN_CMD ?= python manage.py runserver 0.0.0.0:8000
MODEL_RUN_CMD ?= uvicorn model_service.app.main:app --host 0.0.0.0 --port 8010
MIGRATE_CMD ?= python manage.py migrate
SEED_CMD ?= sh -c "python manage.py seed_admin && python manage.py seed_emotions && python manage.py seed_content && python manage.py seed_tree_holes && python manage.py seed_usage_logs && python manage.py seed_model_versions"
TRAIN_BASELINE_CMD ?= sh -c "python -m model_service.training.dataset_builder --raw-dir /app/data/raw --output /tmp/moodflow_emotions.csv && python -m model_service.training.train_baseline --dataset /tmp/moodflow_emotions.csv --output-dir /app/model_service/artifacts/baseline"
BACKEND_TEST_CMD ?= python -m pytest tests -q

.PHONY: help up down logs migrate seed train-baseline run-backend run-model test lint healthcheck

help: ## Show available commands.
	@awk 'BEGIN {FS = ":.*##"; printf "MoodFlow commands:\n"} /^[a-zA-Z_-]+:.*##/ {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

up: ## Build and start MySQL, Redis, backend, and model-service.
	$(COMPOSE) up -d --build

down: ## Stop and remove containers.
	$(COMPOSE) down

logs: ## Follow service logs.
	$(COMPOSE) logs -f

migrate: ## Run Django migrations in the backend container.
	$(COMPOSE) run --rm backend $(MIGRATE_CMD)

seed: ## Seed demo or development data through Django.
	$(COMPOSE) run --rm backend $(SEED_CMD)

train-baseline: ## Train the baseline model in the model-service container.
	$(COMPOSE) run --rm model-service $(TRAIN_BASELINE_CMD)

run-backend: ## Run the backend service with exposed ports.
	$(COMPOSE) run --rm --service-ports backend $(BACKEND_RUN_CMD)

run-model: ## Run the FastAPI model service with exposed ports.
	$(COMPOSE) run --rm --service-ports model-service $(MODEL_RUN_CMD)

test: ## Run backend pytest tests.
	$(COMPOSE) run --rm backend $(BACKEND_TEST_CMD)

lint: ## Run a lightweight Python compile check.
	@set -e; \
	targets=""; \
	[ -d backend ] && targets="$$targets backend"; \
	[ -d model_service ] && targets="$$targets model_service"; \
	[ -d scripts ] && targets="$$targets scripts"; \
	if [ -n "$$targets" ]; then \
		$(PYTHON) -m compileall $$targets; \
	else \
		echo "No Python source directories yet."; \
	fi

healthcheck: ## Check locally exposed backend and model-service endpoints.
	./scripts/healthcheck.sh
