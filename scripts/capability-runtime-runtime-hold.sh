#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_CAPABILITY_RUNTIME_HOLD_SKIP_FULL_CHECK:-}" == "1" ]] && return 0
  [[ "${AION_CAPABILITY_RUNTIME_HOLD_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

nested_gate_context=0
if is_nested_gate_context; then nested_gate_context=1; fi
export AION_CAPABILITY_RUNTIME_HOLD_RUNNING=1

./scripts/capability-runtime-authorization-check.sh
PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"
"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

root = Path(os.environ["AION_REPO_ROOT"])
for relative in (
    "docs/secure-runtime-integration/program-ledger.json",
    "docs/secure-runtime-integration/authorization-ledger.json",
    "examples/secure-runtime-integration/capability-runtime-runtime-hold.json",
):
    payload = json.loads((root / relative).read_text(encoding="utf-8"))
    runtime_authorized = payload.get(
        "capability_runtime_authorized",
        payload.get("sandboxed_capability_runtime_authorized"),
    )
    runtime_implemented = payload.get(
        "capability_runtime_implemented",
        payload.get("sandboxed_capability_runtime_implemented"),
    )
    assert runtime_authorized is True
    assert runtime_implemented is True
    expected_false = (
        "model_output_triggered_execution_enabled",
        "external_connector_execution_enabled",
        "external_tool_execution_enabled",
        "actual_tool_execution_enabled",
        "tool_calling_enabled",
        "function_calling_enabled",
        "public_network_access_enabled",
        "general_network_access_enabled",
        "dns_resolution_enabled",
        "credential_read_enabled",
        "credential_persistence_enabled",
        "token_read_enabled",
        "token_persistence_enabled",
        "filesystem_read_enabled",
        "filesystem_write_enabled",
        "process_spawn_enabled",
        "shell_command_execution_enabled",
        "subprocess_execution_enabled",
        "browser_automation_enabled",
        "dynamic_import_enabled",
        "eval_enabled",
        "exec_enabled",
        "production_write_execution_enabled",
        "production_memory_write_enabled",
        "production_policy_mutation_enabled",
        "actual_belief_creation_enabled",
        "actual_belief_mutation_enabled",
        "production_runtime_authorized",
        "production_exposure",
        "model_weight_training_enabled",
        "v02_release_ready",
    )
    for key in expected_false:
        if key in payload:
            assert payload[key] is False, key
PY

if [[ "$nested_gate_context" == "1" ]]; then
  echo "PASS: full repository check deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/check.sh
fi

echo "sandboxed capability runtime runtime hold PASS"
