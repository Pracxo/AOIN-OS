#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

BASE_URL="${AION_BASE_URL:-${AION_BRAIN_API_URL:-http://localhost:8080}}"
VERSION="$(tr -d '[:space:]' < VERSION)"
SCOPE="${AION_SCOPE:-workspace:main}"
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

verify_args=()
[[ "$KEEP_GOING" == "1" ]] && verify_args+=(--keep-going)
[[ "$OFFLINE_OK" == "1" ]] && verify_args+=(--offline-ok)
[[ "$SKIP_DOCKER" == "1" ]] && verify_args+=(--skip-docker)
[[ "$SKIP_API" == "1" ]] && verify_args+=(--skip-api)

run_step "final verification" ./scripts/v0.1-final-verify.sh "${verify_args[@]}"

release_candidate_status="verified_by_final_verify"
freeze_status="not_run"
release_package_status="not_run"

if [[ "$SKIP_API" == "1" ]]; then
  freeze_status="skipped_by_flag"
  release_package_status="skipped_by_flag"
elif curl -fsS "${BASE_URL}/health" >/dev/null 2>&1; then
  run_step "release package dry-run" curl -fsS \
    -X POST \
    -H "Content-Type: application/json" \
    --data-binary @- \
    "${BASE_URL}/brain/release-package/create" <<JSON
{
  "version": "${VERSION}",
  "owner_scope": ["${SCOPE}"],
  "output_dir": "artifacts/releases",
  "dry_run": true
}
JSON
  release_package_status="dry_run_completed"

  run_step "freeze gate dry-run" curl -fsS \
    -X POST \
    -H "Content-Type: application/json" \
    --data-binary @- \
    "${BASE_URL}/brain/freeze-gate/run" <<JSON
{
  "version": "${VERSION}",
  "owner_scope": ["${SCOPE}"],
  "dry_run": true
}
JSON
  freeze_status="dry_run_completed"
else
  echo
  echo "Brain API is not reachable at ${BASE_URL}; release package and freeze dry-runs were not called."
  if [[ "$OFFLINE_OK" == "1" ]]; then
    freeze_status="skipped_offline"
    release_package_status="skipped_offline"
  else
    freeze_status="blocked_api_unreachable"
    release_package_status="blocked_api_unreachable"
    OVERALL=1
  fi
fi

echo
echo "AION Brain v0.1.0 freeze preview"
echo "release_candidate_status=${release_candidate_status}"
echo "freeze_status=${freeze_status}"
echo "release_package_status=${release_package_status}"
echo "tag_command_preview=git tag aion-v0.1.0"
echo "status=$([[ "$OVERALL" == "0" ]] && echo ready_for_operator_review || echo blocked)"

exit "$OVERALL"
