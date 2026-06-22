#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BASE_URL="${AION_BASE_URL:-http://localhost:8080}"
SCOPE="${AION_SCOPE:-workspace:main}"
PROFILE_KEY="${AION_BOOTSTRAP_PROFILE:-local.dev}"
MODE="dry_run"
RUN_CHECKS=1

for arg in "$@"; do
  case "$arg" in
    --controlled-seed) MODE="controlled" ;;
    --fast) RUN_CHECKS=0 ;;
    --dry-run) MODE="dry_run" ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done

if [[ "$RUN_CHECKS" == "1" ]]; then
  "$ROOT_DIR/scripts/check.sh"
fi

if ! curl -fsS "${BASE_URL}/health" >/dev/null 2>&1; then
  echo "Brain API is not reachable at ${BASE_URL}; start the local stack first." >&2
  echo "Recommended: docker compose up --build" >&2
  exit 1
fi

curl -fsS \
  -X POST \
  -H 'content-type: application/json' \
  "${BASE_URL}/brain/bootstrap/run" \
  --data-binary @- <<JSON
{
  "owner_scope": ["${SCOPE}"],
  "profile_key": "${PROFILE_KEY}",
  "mode": "${MODE}",
  "seed_defaults": true,
  "run_golden_path": false,
  "run_release_smoke": false,
  "run_setup_doctor": true,
  "create_notifications": false,
  "create_operator_items": true,
  "metadata": {
    "script": "bootstrap-local.sh",
    "external_calls": false,
    "package_install": false,
    "source_mutation": false
  }
}
JSON
