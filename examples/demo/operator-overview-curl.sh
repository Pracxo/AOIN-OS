#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${AION_BASE_URL:-http://localhost:8080}"
SCOPE="${AION_SCOPE:-workspace:main}"

curl -fsS "${BASE_URL}/health"
echo
curl -fsS "${BASE_URL}/health/ready"
echo
curl -fsS \
  -X POST \
  -H 'content-type: application/json' \
  "${BASE_URL}/brain/operator/overview" \
  --data-binary @- <<JSON
{"owner_scope":["${SCOPE}"]}
JSON
echo
