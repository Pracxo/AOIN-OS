#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

BASE_URL="${AION_BASE_URL:-${AION_BRAIN_API_URL:-http://localhost:8080}}"
KEEP_GOING=0
OFFLINE_OK=0
SKIP_DOCKER=0
SKIP_API=0
OVERALL=0

for arg in "$@"; do
  case "$arg" in
    --keep-going) KEEP_GOING=1 ;;
    --offline-ok) OFFLINE_OK=1 ;;
    --skip-docker) SKIP_DOCKER=1 ;;
    --skip-api) SKIP_API=1 ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done

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
  OVERALL=1
  if [[ "$KEEP_GOING" != "1" ]]; then
    exit 1
  fi
  return 0
}

offline_arg=()
if [[ "$OFFLINE_OK" == "1" ]]; then
  offline_arg=(--offline-ok)
fi

api_command=()
if [[ "$SKIP_API" == "1" ]]; then
  api_command=(env AION_BASE_URL=http://127.0.0.1:9 AION_BRAIN_API_URL=http://127.0.0.1:9)
fi

run_step "repo check" ./scripts/check.sh
run_step "final docs audit" ./scripts/final-docs-audit.sh
run_step "release candidate gate" "${api_command[@]}" ./scripts/rc-check.sh "${offline_arg[@]}"
run_step "release candidate evidence" "${api_command[@]}" ./scripts/rc-evidence.sh "${offline_arg[@]}"
run_step "golden path" "${api_command[@]}" ./scripts/golden-path.sh "${offline_arg[@]}"
run_step "release smoke" "${api_command[@]}" ./scripts/release-smoke.sh "${offline_arg[@]}"
run_step "setup doctor" "${api_command[@]}" ./scripts/setup-doctor.sh --fast "${offline_arg[@]}"

if [[ "$SKIP_DOCKER" == "1" ]]; then
  echo
  echo "SKIP: docker compose config"
else
  run_step "docker compose config" docker compose config --quiet
fi

run_step "git diff whitespace" git diff --check

if [[ "$SKIP_API" == "1" ]]; then
  echo
  echo "SKIP: API health, readiness, and demo-local"
elif curl -fsS "${BASE_URL}/health" >/dev/null 2>&1; then
  run_step "health endpoint" curl -fsS "${BASE_URL}/health"
  run_step "readiness endpoint" curl -fsS "${BASE_URL}/health/ready"
  run_step "local demo" ./scripts/demo-local.sh "${offline_arg[@]}"
else
  echo
  echo "Brain API is not reachable at ${BASE_URL}."
  if [[ "$OFFLINE_OK" == "1" ]]; then
    echo "Offline mode accepted; API health, readiness, and demo-local skipped."
  else
    OVERALL=1
    if [[ "$KEEP_GOING" != "1" ]]; then
      exit 1
    fi
  fi
fi

echo
echo "AION Brain v0.1.0 final verification summary"
echo "offline_ok=${OFFLINE_OK}"
echo "skip_docker=${SKIP_DOCKER}"
echo "skip_api=${SKIP_API}"
echo "status=$([[ "$OVERALL" == "0" ]] && echo ready || echo blocked)"

exit "$OVERALL"
