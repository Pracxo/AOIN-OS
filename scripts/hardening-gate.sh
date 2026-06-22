#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BASE_URL="${AION_BASE_URL:-${AION_BRAIN_API_URL:-http://localhost:8080}}"
SCOPE="${AION_SECURITY_SCOPE:-workspace:main}"
VERSION="${AION_VERSION:-0.1.0}"

# shellcheck source=scripts/lib/api-response-check.sh
source "$ROOT_DIR/scripts/lib/api-response-check.sh"

if curl -fsS "$BASE_URL/health" >/dev/null 2>&1; then
  RESPONSE_FILE="$(mktemp)"
  trap 'rm -f "$RESPONSE_FILE"' EXIT
  curl --fail-with-body -sS \
    -H "Content-Type: application/json" \
    -d "{\"version\":\"$VERSION\",\"owner_scope\":[\"$SCOPE\"]}" \
    "$BASE_URL/brain/security/hardening-gate/run" \
    -o "$RESPONSE_FILE"
  aion_assert_api_response_ok "hardening gate" "$RESPONSE_FILE"
  cat "$RESPONSE_FILE"
  printf '\n'
else
  echo "AION Brain API is not reachable at $BASE_URL."
  echo "Start the local stack, then rerun ./scripts/hardening-gate.sh."
fi
