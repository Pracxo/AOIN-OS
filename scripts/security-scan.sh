#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BASE_URL="${AION_BASE_URL:-http://localhost:3000}"
SCOPE="${AION_SECURITY_SCOPE:-workspace:dev-workspace}"

if curl -fsS "$BASE_URL/health" >/dev/null 2>&1; then
  curl -fsS \
    -H "Content-Type: application/json" \
    -d "{\"scan_type\":\"full\",\"owner_scope\":[\"$SCOPE\"]}" \
    "$BASE_URL/brain/security/scans/run"
  printf '\n'
else
  echo "AION Brain API is not reachable at $BASE_URL."
  echo "Run ./scripts/test-brain.sh tests/test_secret_scanner.py for local scanner tests."
fi
