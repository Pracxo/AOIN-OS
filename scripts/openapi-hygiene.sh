#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BASE_URL="${AION_BRAIN_API_URL:-http://localhost:8080}"

if curl -fsS "$BASE_URL/health" >/dev/null 2>&1; then
  curl --fail-with-body "$BASE_URL/brain/api/openapi-hygiene"
  exit 0
fi

if [[ -f "$ROOT_DIR/services/brain-api/tests/test_openapi_hygiene.py" ]]; then
  "$ROOT_DIR/scripts/test-brain.sh" tests/test_openapi_hygiene.py
else
  echo "AION server is not reachable and local OpenAPI hygiene test was not found."
fi
