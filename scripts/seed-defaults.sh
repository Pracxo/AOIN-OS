#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${AION_BASE_URL:-http://localhost:8080}"
SCOPE="${AION_SCOPE:-workspace:main}"
MODE="dry_run"

for arg in "$@"; do
  case "$arg" in
    --controlled) MODE="controlled" ;;
    --dry-run) MODE="dry_run" ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done

if ! curl -fsS "${BASE_URL}/health" >/dev/null 2>&1; then
  echo "Brain API is not reachable at ${BASE_URL}; start the local stack first." >&2
  echo "Recommended: docker compose up --build" >&2
  exit 1
fi

curl -fsS \
  -X POST \
  -H 'content-type: application/json' \
  "${BASE_URL}/brain/bootstrap/profiles/seed-defaults" \
  --data-binary @- <<JSON
{"scope": ["${SCOPE}"], "dry_run": true}
JSON

curl -fsS \
  -X POST \
  -H 'content-type: application/json' \
  "${BASE_URL}/brain/bootstrap/seed-bundles/seed-defaults" \
  --data-binary @- <<JSON
{"scope": ["${SCOPE}"], "dry_run": true}
JSON

curl -fsS \
  -X POST \
  -H 'content-type: application/json' \
  "${BASE_URL}/brain/bootstrap/seed" \
  --data-binary @- <<JSON
{
  "owner_scope": ["${SCOPE}"],
  "seed_bundle_key": "core.defaults",
  "mode": "${MODE}",
  "metadata": {
    "script": "seed-defaults.sh",
    "external_calls": false,
    "package_install": false
  }
}
JSON
