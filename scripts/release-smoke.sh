#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${AION_BASE_URL:-http://localhost:8080}"
SCOPE="${AION_SCOPE:-workspace:main}"
OFFLINE_OK=0

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

curl -fsS \
  -X POST \
  "${BASE_URL}/brain/golden-path/release-smoke?scope=${SCOPE}"
