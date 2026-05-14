#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

PYTHON_BIN="${PYTHON:-python3}"
BACKEND_DIR="${BACKEND_DIR:-${PROJECT_ROOT}/backend}"
MANAGE_PY="${MANAGE_PY:-${BACKEND_DIR}/manage.py}"

if [[ ! -f "${MANAGE_PY}" ]]; then
  printf "ERROR: Django manage.py not found at %s\n" "${MANAGE_PY}" >&2
  exit 1
fi

cd "${PROJECT_ROOT}"

django_manage() {
  (
    cd "${BACKEND_DIR}"
    "${PYTHON_BIN}" "${MANAGE_PY}" "$@"
  )
}

command_exists() {
  local command_name="$1"
  grep -Eq "^[[:space:]]*${command_name}$" <<<"${AVAILABLE_COMMANDS}"
}

run_optional_command() {
  local command_name="$1"

  if command_exists "${command_name}"; then
    printf "\n==> Running %s\n" "${command_name}"
    django_manage "${command_name}"
  else
    printf "\n==> Skipping %s: Django management command not found.\n" "${command_name}"
  fi
}

printf "==> Running Django migrations\n"
django_manage migrate

AVAILABLE_COMMANDS="$(django_manage help --commands)"
SEED_COMMANDS=(
  seed_admin
  seed_emotions
  seed_content
  seed_tree_holes
  seed_usage_logs
  seed_model_versions
)

for seed_command in "${SEED_COMMANDS[@]}"; do
  run_optional_command "${seed_command}"
done
