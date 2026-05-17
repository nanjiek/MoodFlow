#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

PYTHON_BIN="${PYTHON:-python3}"
RAW_DATA_DIR="${RAW_DATA_DIR:-data/raw}"
DATASET_PATH="${DATASET_PATH:-data/processed/moodflow_emotions.csv}"
MODEL_OUTPUT_DIR="${MODEL_OUTPUT_DIR:-model_service/artifacts/baseline-clean-v4}"
MODEL_METADATA_PATH="${MODEL_METADATA_PATH:-${MODEL_OUTPUT_DIR}/metadata.json}"

BACKEND_DIR="${BACKEND_DIR:-${PROJECT_ROOT}/backend}"
MANAGE_PY="${MANAGE_PY:-${BACKEND_DIR}/manage.py}"
IMPORT_TRAINING_SAMPLES_COMMAND="${IMPORT_TRAINING_SAMPLES_COMMAND:-import_training_samples}"
REGISTER_MODEL_VERSION_COMMAND="${REGISTER_MODEL_VERSION_COMMAND:-seed_model_versions}"

cd "${PROJECT_ROOT}"

django_manage() {
  (
    cd "${BACKEND_DIR}"
    "${PYTHON_BIN}" "${MANAGE_PY}" "$@"
  )
}

load_django_commands() {
  if [[ ! -f "${MANAGE_PY}" ]]; then
    return 0
  fi

  django_manage help --commands 2>/dev/null || true
}

django_command_exists() {
  local command_name="$1"
  grep -Eq "^[[:space:]]*${command_name}$" <<<"${AVAILABLE_DJANGO_COMMANDS}"
}

run_optional_django_command() {
  local command_name="$1"
  shift

  if django_command_exists "${command_name}"; then
    printf "\n==> Running %s\n" "${command_name}"
    django_manage "${command_name}" "$@"
  else
    printf "\n==> Skipping %s: Django management command not found.\n" "${command_name}"
  fi
}

printf "==> Building training dataset\n"
"${PYTHON_BIN}" -m model_service.training.dataset_builder \
  --raw-dir "${RAW_DATA_DIR}" \
  --output "${DATASET_PATH}"

printf "\n==> Training baseline model\n"
"${PYTHON_BIN}" -m model_service.training.train_baseline \
  --dataset "${DATASET_PATH}" \
  --output-dir "${MODEL_OUTPUT_DIR}"

AVAILABLE_DJANGO_COMMANDS="$(load_django_commands)"

run_optional_django_command \
  "${IMPORT_TRAINING_SAMPLES_COMMAND}" \
  --path "${DATASET_PATH}"

run_optional_django_command \
  "${REGISTER_MODEL_VERSION_COMMAND}" \
  --metadata "${MODEL_METADATA_PATH}"
