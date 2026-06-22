#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BASE_URL="${AION_BASE_URL:-http://localhost:8080}"
SCOPE="${AION_SCOPE:-workspace:main}"
RUN_CHECKS=1

for arg in "$@"; do
  case "$arg" in
    --fast) RUN_CHECKS=0 ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done

test -f "$ROOT_DIR/.env.example"
test -x "$ROOT_DIR/scripts/check.sh"
test -x "$ROOT_DIR/scripts/golden-path.sh"
test -x "$ROOT_DIR/scripts/release-smoke.sh"

docker compose -f "$ROOT_DIR/docker-compose.yml" config >/dev/null

if [[ "$RUN_CHECKS" == "1" ]]; then
  "$ROOT_DIR/scripts/check.sh"
fi

if curl -fsS "${BASE_URL}/health" >/dev/null 2>&1; then
  curl -fsS \
    -X POST \
    -H 'content-type: application/json' \
    "${BASE_URL}/brain/bootstrap/doctor" \
    --data-binary @- <<JSON
{
  "owner_scope": ["${SCOPE}"],
  "include_golden_path": false,
  "include_release_smoke": false,
  "create_findings": true,
  "metadata": {
    "script": "setup-doctor.sh",
    "external_calls": false,
    "package_install": false,
    "shell_execution": false
  }
}
JSON
else
  echo "Brain API is not reachable at ${BASE_URL}; local file and compose checks passed."
fi
