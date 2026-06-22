#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
API_URL="${AION_BASE_URL:-http://localhost:8080}"
OFFLINE_OK=0
SKIP_DOCKER=0
SKIP_RC=0
SKIP_GOLDEN=0
KEEP_GOING=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --offline-ok) OFFLINE_OK=1; shift ;;
    --skip-docker) SKIP_DOCKER=1; shift ;;
    --skip-rc) SKIP_RC=1; shift ;;
    --skip-golden) SKIP_GOLDEN=1; shift ;;
    --keep-going) KEEP_GOING=1; shift ;;
    --api-url)
      API_URL="${2:?--api-url requires a value}"
      shift 2
      ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

cd "$ROOT_DIR"

echo "AION v0.1 local demo"
echo "API: ${API_URL}"

run_step() {
  local name="$1"
  shift
  echo
  echo "==> ${name}"
  if "$@"; then
    echo "PASS: ${name}"
    return 0
  fi
  echo "FAIL: ${name}" >&2
  if [[ "$KEEP_GOING" == "1" ]]; then
    return 0
  fi
  return 1
}

api_reachable() {
  curl -fsS "${API_URL}/health" >/dev/null 2>&1
}

if [[ "$SKIP_DOCKER" != "1" ]]; then
  run_step "docker compose config" docker compose config --quiet
fi

if api_reachable; then
  run_step "health" curl -fsS "${API_URL}/health"
  run_step "readiness" curl -fsS "${API_URL}/health/ready"
else
  if [[ "$OFFLINE_OK" == "1" ]]; then
    echo "Brain API is not reachable at ${API_URL}; continuing offline."
  else
    echo "Brain API is not reachable at ${API_URL}." >&2
    exit 1
  fi
fi

AION_BASE_URL="$API_URL" run_step "setup doctor" ./scripts/setup-doctor.sh --fast --offline-ok

if [[ "$SKIP_GOLDEN" != "1" ]]; then
  AION_BASE_URL="$API_URL" run_step "golden path" ./scripts/golden-path.sh --offline-ok
fi

if [[ "$SKIP_RC" != "1" ]]; then
  AION_BASE_URL="$API_URL" run_step "RC gate" ./scripts/rc-check.sh --offline-ok
fi

if api_reachable; then
  run_step "extension manifest validation" \
    curl -fsS -X POST -H 'content-type: application/json' \
      "${API_URL}/brain/extensions/manifests/validate" \
      --data-binary @examples/demo/generic-extension-manifest.json
  run_step "release smoke" \
    curl -fsS -X POST "${API_URL}/brain/golden-path/release-smoke?scope=workspace:main"
  run_step "operator overview" \
    curl -fsS -X POST -H 'content-type: application/json' \
      "${API_URL}/brain/operator/overview" \
      --data-binary '{"owner_scope":["workspace:main"]}'
else
  echo "Skipping API-backed extension, release smoke, and operator overview demo steps."
fi

echo
echo "Next commands:"
echo "  ./scripts/rc-evidence.sh --offline-ok"
echo "  ./scripts/final-docs-audit.sh"
echo "  docker compose down"
