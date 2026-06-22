#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${AION_BASE_URL:-${AION_API_URL:-http://localhost:8080}}"
SCOPE="${AION_RESILIENCE_SCOPE:-workspace:dev-workspace}"

if curl -fsS "$BASE_URL/health" >/dev/null 2>&1; then
  curl -fsS \
    -H "Content-Type: application/json" \
    -X POST \
    -d "{\"owner_scope\":[\"$SCOPE\"],\"mode\":\"dry_run\",\"include_fault_injection\":false}" \
    "$BASE_URL/brain/resilience/test/run"
  printf '\n'
else
  echo "AION Brain API is not reachable at $BASE_URL."
  echo "Start the local stack, then rerun ./scripts/resilience-check.sh."
fi
