#!/usr/bin/env bash
set -euo pipefail

API_URL="${AION_API_URL:-http://localhost:8080}"
SCOPE="${AION_SCOPE:-workspace:dev-workspace}"
VERSION="${AION_PERFORMANCE_BASELINE_VERSION:-0.1.0}"
BASELINE_NAME="${AION_BASELINE_NAME:-local-baseline}"

if ! curl -fsS "$API_URL/health" >/dev/null 2>&1; then
  echo "AION Brain API is not reachable at $API_URL"
  exit 1
fi

RUN_RESPONSE=$(SCOPE="$SCOPE" API_URL="$API_URL" "$PWD/scripts/benchmark-local.sh")
RUN_ID=$(printf '%s' "$RUN_RESPONSE" | python -c 'import json,sys; print(json.load(sys.stdin)["benchmark_run_id"])')
BODY=$(printf '{"version":"%s","baseline_name":"%s","benchmark_run_ids":["%s"]}' "$VERSION" "$BASELINE_NAME" "$RUN_ID")

curl -fsS \
  -H "Content-Type: application/json" \
  -X POST \
  "$API_URL/brain/performance/baselines/from-runs" \
  -d "$BODY"
