#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BASE_URL="${AION_BASE_URL:-http://localhost:8080}"
SCOPE="${AION_SCOPE:-workspace:main}"
KEEP_GOING=0
OFFLINE_OK=0

# shellcheck source=scripts/lib/api-response-check.sh
source "$ROOT_DIR/scripts/lib/api-response-check.sh"

for arg in "$@"; do
  case "$arg" in
    --keep-going) KEEP_GOING=1 ;;
    --offline-ok) OFFLINE_OK=1 ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done

RESULTS_FILE="$(mktemp)"
SEED_RESPONSE_FILE="$(mktemp)"
GATE_RESPONSE_FILE="$(mktemp)"
trap 'rm -f "$RESULTS_FILE" "$SEED_RESPONSE_FILE" "$GATE_RESPONSE_FILE"' EXIT
printf '[\n' >"$RESULTS_FILE"
FIRST_RESULT=1
OVERALL=0

run_check() {
  local key="$1"
  local command_hint="$2"
  shift 2
  local start end duration status summary passed severity
  start="$(date +%s)"
  if "$@"; then
    status="passed"
    summary="${key} passed."
  else
    status="failed"
    summary="${key} failed."
    OVERALL=1
  fi
  passed="$([[ "$status" == "passed" ]] && echo true || echo false)"
  severity="$([[ "$status" == "passed" ]] && echo low || echo critical)"
  end="$(date +%s)"
  duration=$(( (end - start) * 1000 ))
  if [[ "$FIRST_RESULT" == "0" ]]; then
    printf ',\n' >>"$RESULTS_FILE"
  fi
  FIRST_RESULT=0
  printf '  {"verification_check_id":"rc-script-%s","trace_id":null,"rc_run_id":null,"check_key":"%s","check_type":"generic","status":"%s","severity":"%s","required":true,"passed":%s,"title":"%s","summary":"%s","command_hint":"%s","duration_ms":%s,"evidence":{"script":"rc-check.sh","external_calls":false,"source_mutation":false},"error":{},"metadata":{},"created_at":null}\n' \
    "${key//./-}" \
    "$key" \
    "$status" \
    "$severity" \
    "$passed" \
    "$key" \
    "$summary" \
    "$command_hint" \
    "$duration" >>"$RESULTS_FILE"
  if [[ "$status" != "passed" && "$KEEP_GOING" == "0" ]]; then
    printf '\n]\n' >>"$RESULTS_FILE"
    return 1
  fi
  return 0
}

run_check "no_domain_drift" "scripts/verify-no-domain-drift.sh" "$ROOT_DIR/scripts/verify-no-domain-drift.sh" || exit 1
run_check "lint" "scripts/lint.sh" "$ROOT_DIR/scripts/lint.sh" || exit 1
run_check "tests.brain" "scripts/test-brain.sh" "$ROOT_DIR/scripts/test-brain.sh" || exit 1
run_check "tests.sdk" "scripts/test-sdk.sh" "$ROOT_DIR/scripts/test-sdk.sh" || exit 1
run_check "typecheck" "scripts/typecheck.sh" "$ROOT_DIR/scripts/typecheck.sh" || exit 1
run_check "policy_coverage" "scripts/policy-coverage.sh" "$ROOT_DIR/scripts/policy-coverage.sh" || exit 1
run_check "openapi_hygiene" "scripts/openapi-hygiene.sh" "$ROOT_DIR/scripts/openapi-hygiene.sh" || exit 1
run_check "boundary_check" "scripts/boundary-check.sh" "$ROOT_DIR/scripts/boundary-check.sh" || exit 1
run_check "repo_health" "scripts/repo-health.sh" "$ROOT_DIR/scripts/repo-health.sh" || exit 1
run_check "docker_compose_config" "docker compose config --quiet" docker compose -f "$ROOT_DIR/docker-compose.yml" config --quiet || exit 1
run_check "bootstrap_doctor" "scripts/setup-doctor.sh --fast --offline-ok" "$ROOT_DIR/scripts/setup-doctor.sh" --fast --offline-ok || exit 1

printf '\n]\n' >>"$RESULTS_FILE"

if curl -fsS "${BASE_URL}/health" >/dev/null 2>&1; then
  if ! curl -fsS \
    -X POST \
    -H 'content-type: application/json' \
    "${BASE_URL}/brain/rc/matrices/seed-defaults" \
    --data-binary @- \
    -o "$SEED_RESPONSE_FILE" <<JSON
{"scope":["${SCOPE}"],"dry_run":true,"created_by":"rc-check.sh"}
JSON
  then
    echo "RC matrix endpoint failed at ${BASE_URL} after API health succeeded." >&2
    exit 1
  fi
  aion_assert_api_response_ok "RC matrix seed" "$SEED_RESPONSE_FILE"
  cat "$SEED_RESPONSE_FILE"
  echo

  CHECK_RESULTS="$(cat "$RESULTS_FILE")"
  if ! curl -fsS \
    -X POST \
    -H 'content-type: application/json' \
    "${BASE_URL}/brain/rc/gate/run" \
    --data-binary @- \
    -o "$GATE_RESPONSE_FILE" <<JSON
{
  "owner_scope": ["${SCOPE}"],
  "rc_key": "rc.local.script",
  "mode": "dry_run",
  "run_service_checks": true,
  "include_docker_smoke": false,
  "check_results": ${CHECK_RESULTS},
  "metadata": {
    "script": "rc-check.sh",
    "external_calls": false,
    "deployment": false,
    "publish": false,
    "source_mutation": false
  },
  "created_by": "rc-check.sh"
}
JSON
  then
    echo "RC gate endpoint failed at ${BASE_URL} after API health succeeded." >&2
    exit 1
  fi
  aion_assert_api_response_ok "RC gate" "$GATE_RESPONSE_FILE"
  cat "$GATE_RESPONSE_FILE"
  echo
else
  if [[ "$OFFLINE_OK" == "1" ]]; then
    echo "Brain API is not reachable at ${BASE_URL}; local RC checks completed offline."
  else
    echo "Brain API is not reachable at ${BASE_URL}." >&2
    OVERALL=1
  fi
fi

exit "$OVERALL"
