#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${AION_BASE_URL:-http://localhost:3000}"
SCOPE="${AION_SECURITY_SCOPE:-workspace:dev-workspace}"
VERSION="${AION_VERSION:-0.1.0}"

if curl -fsS "$BASE_URL/health" >/dev/null 2>&1; then
  curl -fsS \
    -H "Content-Type: application/json" \
    -d "{\"version\":\"$VERSION\",\"owner_scope\":[\"$SCOPE\"]}" \
    "$BASE_URL/brain/security/hardening-gate/run"
  printf '\n'
else
  echo "AION Brain API is not reachable at $BASE_URL."
  echo "Start the local stack, then rerun ./scripts/hardening-gate.sh."
fi
