#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_OPERATOR_CONSOLE_INTEGRATION_RUNTIME_HOLD_SKIP_FULL_CHECK:-}" == "1" ]] && return 0
  [[ "${AION_OPERATOR_CONSOLE_INTEGRATION_RUNTIME_HOLD_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

nested_gate_context=0
if is_nested_gate_context; then nested_gate_context=1; fi
export AION_OPERATOR_CONSOLE_INTEGRATION_RUNTIME_HOLD_RUNNING=1

./scripts/operator-console-integration-authorization-check.sh

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

root = Path(os.environ["AION_REPO_ROOT"])
hold = json.loads(
    (root / "examples/secure-runtime-integration/operator-console-runtime-hold.json").read_text()
)
for key in (
    "public_listener_enabled",
    "external_network_egress_enabled",
    "browser_persistence_enabled",
    "actual_model_provider_call_enabled",
    "external_connector_execution_enabled",
    "actual_tool_execution_enabled",
    "production_runtime_authorized",
    "production_deployment_enabled",
    "model_weight_training_enabled",
    "v02_release_ready",
):
    if hold[key] is not False:
        raise SystemExit(f"runtime hold mismatch: {key}")
for key in (
    "operator_console_integration_implemented",
    "integrated_authenticated_local_pilot_completed",
    "local_loopback_listener_available",
    "same_origin_static_asset_serving_available",
    "loopback_listener_absent",
    "listener_inactive_outside_explicit_runner_invocation",
    "authorization_active",
):
    if hold[key] is not True:
        raise SystemExit(f"runtime hold true flag mismatch: {key}")
if hold["authorization_consumed"] is not False:
    raise SystemExit("AION-236-SRI-0004 must remain active pending AION-238")
PY

if [[ "$nested_gate_context" == "1" ]]; then
  echo "PASS: full repository check deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 AION_CHECK_RUNNING=1 ./scripts/check.sh
fi

echo "controlled operator console integration runtime hold PASS"
