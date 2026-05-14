#!/usr/bin/env sh
set -eu

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
MODEL_SERVICE_URL="${MODEL_SERVICE_URL:-http://localhost:8010}"

check_http() {
  name="$1"
  base_url="$2"
  shift 2

  for path in "$@"; do
    if curl -fsS "${base_url}${path}" >/dev/null 2>&1; then
      printf "%s OK (%s%s)\n" "$name" "$base_url" "$path"
      return 0
    fi
  done

  printf "%s FAIL (%s)\n" "$name" "$base_url" >&2
  return 1
}

check_http "backend" "$BACKEND_URL" /api/health/ /api/health
check_http "model-service" "$MODEL_SERVICE_URL" /health /health/ /docs
