#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_LIVE_PROVIDER_PILOT_RUNTIME_HOLD_SKIP_FULL_CHECK:-}" == "1" ]] && return 0
  [[ "${AION_LIVE_PROVIDER_PILOT_RUNTIME_HOLD_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

nested_gate_context=0
if is_nested_gate_context; then
  nested_gate_context=1
fi
export AION_LIVE_PROVIDER_PILOT_RUNTIME_HOLD_RUNNING=1

./scripts/live-provider-pilot-authorization-no-go-regression.sh
./scripts/live-provider-pilot-authorization-check.sh

if [[ "$nested_gate_context" == "1" ]]; then
  echo "PASS: full repository check deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/check.sh
fi

echo "live provider pilot runtime hold PASS"
