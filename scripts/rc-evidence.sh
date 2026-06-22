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
    echo "Brain API is not reachable at ${BASE_URL}; skipping RC evidence fetch."
    exit 0
  fi
  echo "Brain API is not reachable at ${BASE_URL}." >&2
  exit 1
fi

fetch_json_evidence() {
  local label="$1"
  local url="$2"
  local response_file
  local status_file
  local curl_status
  local http_status

  response_file="$(mktemp)"
  status_file="$(mktemp)"
  if curl -sS -o "$response_file" -w "%{http_code}" "$url" >"$status_file"; then
    curl_status=0
  else
    curl_status=$?
  fi
  http_status="$(cat "$status_file")"
  rm -f "$status_file"

  if [[ "$curl_status" != "0" ]]; then
    rm -f "$response_file"
    if [[ "$OFFLINE_OK" == "1" ]]; then
      echo "${label} endpoint is unavailable at ${BASE_URL}; skipping evidence fetch."
      return 0
    fi
    echo "${label} endpoint is unavailable at ${BASE_URL}." >&2
    return 1
  fi

  if [[ "$http_status" == "404" && "$OFFLINE_OK" == "1" ]]; then
    rm -f "$response_file"
    echo "${label} endpoint is not available at ${BASE_URL}; skipping evidence fetch."
    return 0
  fi

  if [[ ! "$http_status" =~ ^2 ]]; then
    cat "$response_file" >&2 || true
    rm -f "$response_file"
    echo "${label} endpoint returned HTTP ${http_status}." >&2
    return 1
  fi

  aion_assert_api_response_ok "$label" "$response_file"
  cat "$response_file"
  rm -f "$response_file"
}

echo "Latest RC reports:"
fetch_json_evidence "RC reports" "${BASE_URL}/brain/rc/reports?scope=${SCOPE}&limit=1"
echo
echo "Latest RC evidence packs:"
fetch_json_evidence "RC evidence packs" "${BASE_URL}/brain/rc/evidence-packs?scope=${SCOPE}&limit=1"
echo
