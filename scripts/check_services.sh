#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
MODEL_SERVICE_URL="${MODEL_SERVICE_URL:-http://localhost:8010}"
CHECK_TIMEOUT_SECONDS="${CHECK_TIMEOUT_SECONDS:-5}"
CURL_BIN="${CURL:-curl}"

cd "${PROJECT_ROOT}"

check_endpoint() {
  local name="$1"
  local base_url="$2"
  local path="$3"
  local url="${base_url%/}${path}"

  if "${CURL_BIN}" -fsS --max-time "${CHECK_TIMEOUT_SECONDS}" "${url}" >/dev/null; then
    printf "%s OK (%s)\n" "${name}" "${url}"
    return 0
  fi

  printf "%s FAIL (%s)\n" "${name}" "${url}" >&2
  return 1
}

status=0
check_endpoint "backend" "${BACKEND_URL}" "/api/health/" || status=1
check_endpoint "model-service" "${MODEL_SERVICE_URL}" "/health" || status=1
exit "${status}"
