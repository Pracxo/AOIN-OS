#!/usr/bin/env bash
set -euo pipefail

AION_BRAIN_API_URL="${AION_BRAIN_API_URL:-http://localhost:3000}"
AION_WORKFLOW_MAX_RUNS="${AION_WORKFLOW_MAX_RUNS:-1}"

curl -sS \
  -X POST \
  "${AION_BRAIN_API_URL}/brain/workflows/worker/start-once" \
  -H "content-type: application/json" \
  -d "{\"max_runs\":${AION_WORKFLOW_MAX_RUNS}}"
