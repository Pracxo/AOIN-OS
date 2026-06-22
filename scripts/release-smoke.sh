#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BASE_URL="${AION_BASE_URL:-http://localhost:8080}"
SCOPE="${AION_SCOPE:-workspace:main}"
OFFLINE_OK=0

# shellcheck source=scripts/lib/api-response-check.sh
source "$ROOT_DIR/scripts/lib/api-response-check.sh"

for arg in "$@"; do
  case "$arg" in
    --offline-ok) OFFLINE_OK=1 ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done

if ! curl -fsS "${BASE_URL}/health" >/dev/null 2>&1; then
  if [[ "$OFFLINE_OK" == "1" ]]; then
    echo "Brain API is not reachable at ${BASE_URL}; skipping release smoke."
    exit 0
  fi
  echo "Brain API is not reachable at ${BASE_URL}." >&2
  exit 1
fi

RESPONSE_FILE="$(mktemp)"
trap 'rm -f "$RESPONSE_FILE"' EXIT

curl -fsS \
  -X POST \
  "${BASE_URL}/brain/golden-path/release-smoke?scope=${SCOPE}" \
  -o "$RESPONSE_FILE"
aion_assert_api_response_ok "release smoke" "$RESPONSE_FILE"
cat "$RESPONSE_FILE"
