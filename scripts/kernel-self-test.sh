#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${AION_BRAIN_API_URL:-http://localhost:8080}"

if ! curl -fsS "$BASE_URL/health" >/dev/null 2>&1; then
  echo "AION server is not reachable. Start it with scripts/docker-up-core.sh."
  exit 0
fi

curl --fail-with-body \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{"scope":["workspace:dev-workspace"],"dry_run":true}' \
  "$BASE_URL/brain/kernel/self-test"
