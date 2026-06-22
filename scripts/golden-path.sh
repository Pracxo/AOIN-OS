#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${AION_BASE_URL:-http://localhost:3000}"
SCOPE="${AION_SCOPE:-workspace:main}"

curl -fsS \
  -X POST \
  -H 'content-type: application/json' \
  "${BASE_URL}/brain/golden-path/run" \
  --data-binary @- <<JSON
{
  "owner_scope": ["${SCOPE}"],
  "mode": "dry_run",
  "run_all_defaults": true,
  "create_notifications": false,
  "create_operator_items": true,
  "include_release_smoke": true,
  "metadata": {
    "script": "golden-path.sh",
    "external_calls": false,
    "tool_execution": false
  }
}
JSON
