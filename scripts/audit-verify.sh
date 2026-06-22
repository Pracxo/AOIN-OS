#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${AION_BASE_URL:-http://localhost:3000}"

if ! curl -fsS "${BASE_URL}/health" >/dev/null 2>&1; then
  echo "AION Brain API is not reachable at ${BASE_URL}. Start the server first."
  exit 1
fi

curl -fsS \
  -X POST \
  "${BASE_URL}/brain/audit/verify" \
  -H "content-type: application/json" \
  -d '{"metadata":{"source":"scripts/audit-verify.sh"}}'
