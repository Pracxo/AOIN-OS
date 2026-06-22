#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${AION_BASE_URL:-http://localhost:8080}"
SCOPE="${AION_RUNTIME_CONFIG_SCOPE:-workspace:dev-workspace}"

if curl -fsS "$BASE_URL/health" >/dev/null 2>&1; then
  curl -fsS \
    -H "Content-Type: application/json" \
    -d "{\"owner_scope\":[\"$SCOPE\"]}" \
    "$BASE_URL/brain/runtime-config/validate"
  printf '\n'
else
  echo "AION Brain API is not reachable at $BASE_URL."
  echo "Start the local stack, then rerun ./scripts/config-validate.sh."
fi
