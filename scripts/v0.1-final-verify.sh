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
declare -a offline_arg=()
declare -a api_command=()
declare -a api_ready_command=()

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

run_api_step() {
  local name="$1"
  shift
  if (( ${#api_command[@]} > 0 )); then
    run_step "$name" "${api_command[@]}" "$@"
  else
    run_step "$name" "$@"
  fi
}

run_api_ready_step() {
  local name="$1"
  shift
  if (( ${#api_ready_command[@]} > 0 )); then
    run_step "$name" "${api_ready_command[@]}" "$@"
  else
    run_step "$name" "$@"
  fi
}

run_api_step_with_offline_flag() {
  local name="$1"
  shift
  if [[ "$OFFLINE_OK" == "1" ]]; then
    run_api_step "$name" "$@" --offline-ok
  else
    run_api_step "$name" "$@"
  fi
}

run_step_with_offline_flag() {
  local name="$1"
  shift
  if [[ "$OFFLINE_OK" == "1" ]]; then
    run_step "$name" "$@" --offline-ok
  else
    run_step "$name" "$@"
  fi
}

skip_step() {
  local name="$1"
  echo
  echo "SKIP: ${name}"
}

run_repo_check() {
  if [[ "$SKIP_API" == "1" ]]; then
    run_step "no-domain drift" ./scripts/verify-no-domain-drift.sh
    run_step "lint" ./scripts/lint.sh
    run_step "brain tests" ./scripts/test-brain.sh
    run_step "sdk tests" ./scripts/test-sdk.sh
    run_step "typecheck" ./scripts/typecheck.sh
    run_step "boundary check local tests" ./scripts/test-brain.sh \
      tests/test_no_direct_vendor_leakage.py \
      tests/test_architecture_boundary_check.py
    run_step "repo health" ./scripts/repo-health.sh
  else
    run_step "repo check" ./scripts/check.sh
  fi
}

run_repo_check
run_step "final docs audit" ./scripts/final-docs-audit.sh

if [[ "$SKIP_API" == "1" ]]; then
  skip_step "release candidate gate API phase"
  skip_step "release candidate evidence"
  skip_step "golden path API run"
  skip_step "release smoke API run"
  skip_step "setup doctor API run"
else
  run_api_step_with_offline_flag "release candidate gate" ./scripts/rc-check.sh
  run_api_step_with_offline_flag "release candidate evidence" ./scripts/rc-evidence.sh
  run_api_step_with_offline_flag "golden path" ./scripts/golden-path.sh
  run_api_step_with_offline_flag "release smoke" ./scripts/release-smoke.sh
  run_api_step_with_offline_flag "setup doctor" ./scripts/setup-doctor.sh --fast
fi

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
  run_api_ready_step "health endpoint" curl -fsS "${BASE_URL}/health"
  run_api_ready_step "readiness endpoint" curl -fsS "${BASE_URL}/health/ready"
  run_step_with_offline_flag "local demo" ./scripts/demo-local.sh
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
