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
./scripts/live-provider-pilot-no-go-regression.sh

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
program = json.loads((ROOT / "docs/adaptive-intelligence/program-ledger.json").read_text())
hold = json.loads((ROOT / "examples/adaptive-intelligence/live-provider-pilot-runtime-hold.json").read_text())

if program.get("active_adaptive_intelligence_authorization") != "AION-247-AI-0002":
    raise SystemExit("AION-248 runtime hold active authorization mismatch")
if program.get("formal_closeout_task") != "AION-249":
    raise SystemExit("AION-248 runtime hold closeout task mismatch")
if hold.get("live_provider_pilot_implemented") is not True:
    raise SystemExit("AION-248 runtime hold implementation marker missing")
if hold.get("live_provider_pilot_completed") is True:
    required_completed_state = (
        "implemented_operator_invoked_synthetic_pilot_complete_pending_AION-249_closeout"
    )
    if program.get("live_provider_pilot_state") != required_completed_state:
        raise SystemExit("AION-248 completed runtime hold state mismatch")
else:
    if hold.get("live_provider_pilot_state") != "implementation_ready_live_execution_pending":
        raise SystemExit("AION-248 pending runtime hold state mismatch")

for key in (
    "provider_runtime_active",
    "network_runtime_active",
    "credential_read_currently_enabled",
    "authorization_header_creation_currently_enabled",
    "raw_prompt_persistence_enabled",
    "raw_response_persistence_enabled",
    "memory_write_enabled",
    "tool_execution_enabled",
    "connector_execution_enabled",
    "background_loops_enabled",
    "production_runtime_authorized",
):
    if hold.get(key) is not False:
        raise SystemExit(f"AION-248 runtime hold violation: {key}")

print("OpenAI live provider pilot runtime hold PASS")
PY

if [[ "$nested_gate_context" == "1" ]]; then
  echo "PASS: full repository check deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/check.sh
fi

echo "live provider pilot runtime hold PASS"
