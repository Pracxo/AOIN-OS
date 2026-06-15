#!/usr/bin/env bash
set -euo pipefail

API_URL="${AION_API_URL:-http://localhost:8080}"
SCOPE="${AION_SCOPE:-workspace:dev-workspace}"
BENCHMARK_ID="${BENCHMARK_ID:-}"

if ! curl -fsS "$API_URL/health" >/dev/null 2>&1; then
  echo "AION Brain API is not reachable at $API_URL"
  exit 1
fi

if [[ -n "$BENCHMARK_ID" ]]; then
  BODY=$(printf '{"benchmark_id":"%s","owner_scope":["%s"],"mode":"dry_run","repeat":1}' "$BENCHMARK_ID" "$SCOPE")
else
  BODY=$(printf '{"benchmark":{"benchmark_id":"local-full","name":"Local full benchmark","description":"Local deterministic benchmark.","status":"active","benchmark_type":"full_local","owner_scope":["%s"],"steps":[{"step_id":"noop","operation_type":"noop","description":"Local no-op.","repeat":1,"expected_status":"passed","required":true}],"thresholds":{"default_threshold_ms":1000},"metadata":{"local_only":true,"external_calls":false}},"owner_scope":["%s"],"mode":"dry_run","repeat":1}' "$SCOPE" "$SCOPE")
fi

curl -fsS \
  -H "Content-Type: application/json" \
  -X POST \
  "$API_URL/brain/performance/benchmarks/run" \
  -d "$BODY"
