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
    echo "Brain API is not reachable at ${BASE_URL}; skipping RC evidence fetch."
    exit 0
  fi
  echo "Brain API is not reachable at ${BASE_URL}." >&2
  exit 1
fi

echo "Latest RC reports:"
if ! curl -fsS "${BASE_URL}/brain/rc/reports?scope=${SCOPE}&limit=1"; then
  if [[ "$OFFLINE_OK" == "1" ]]; then
    echo "RC report endpoint is unavailable at ${BASE_URL}; skipping evidence fetch."
    exit 0
  fi
  exit 1
fi
echo
echo "Latest RC evidence packs:"
if ! curl -fsS "${BASE_URL}/brain/rc/evidence-packs?scope=${SCOPE}&limit=1"; then
  if [[ "$OFFLINE_OK" == "1" ]]; then
    echo "RC evidence-pack endpoint is unavailable at ${BASE_URL}; skipping evidence fetch."
    exit 0
  fi
  exit 1
fi
echo
