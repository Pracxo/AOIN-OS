#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_ADAPTIVE_INTELLIGENCE_RUNTIME_HOLD_SKIP_FULL_CHECK:-}" == "1" ]] && return 0
  [[ "${AION_ADAPTIVE_INTELLIGENCE_AUTHORIZATION_CHECK_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
export AION_BRAIN_PYTHON="$PYTHON_BIN"

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path.cwd()
AUTHORIZED_STATE = "adaptive_intelligence_program_authorized_not_implemented"
IMPLEMENTED_DISABLED_STATE = (
    "external_cognition_gateway_foundation_implemented_disabled_pending_AION-247_closeout"
)
program = json.loads((ROOT / "docs/adaptive-intelligence/program-ledger.json").read_text(encoding="utf-8"))
hold = json.loads((ROOT / "examples/adaptive-intelligence/runtime-hold.json").read_text(encoding="utf-8"))

if program.get("program_state") not in {AUTHORIZED_STATE, IMPLEMENTED_DISABLED_STATE}:
    raise SystemExit("adaptive intelligence runtime hold program state mismatch")

required = {
    "adaptive_intelligence_program_authorized": True,
    "adaptive_intelligence_program_implemented": False,
    "active_adaptive_intelligence_authorization": "AION-245-AI-0001",
    "active_adaptive_intelligence_task": "AION-246",
    "formal_closeout_task": "AION-247",
    "production_runtime_authorized": False,
}
for key, value in required.items():
    if program.get(key) != value and hold.get(key) != value:
        raise SystemExit(f"runtime hold mismatch {key}")

if program.get("program_state") == IMPLEMENTED_DISABLED_STATE:
    for key, value in {
        "external_cognition_gateway_implemented": True,
        "external_cognition_gateway_state": "implemented_disabled_deterministic_fixture_only_pending_AION-247_closeout",
        "deterministic_fixture_pilot_completed": True,
    }.items():
        if program.get(key) != value:
            raise SystemExit(f"adaptive intelligence runtime hold mismatch {key}")
else:
    if program.get("external_cognition_gateway_implemented") is not False:
        raise SystemExit("external cognition gateway cannot be implemented in pre-implementation hold")

zero_keys = {
    "actual_provider_calls",
    "public_network_calls",
    "external_network_egress_calls",
    "dns_resolutions",
    "provider_credentials_read",
    "provider_tokens_read",
    "authorization_headers_created",
    "persistent_memory_writes",
    "verified_knowledge_promotions",
    "belief_mutations",
    "external_tool_executions",
    "external_connector_calls",
    "autonomous_background_cycles",
    "source_mutations",
    "git_operations",
    "production_deployments",
    "model_weight_changes",
}
for key in zero_keys:
    if hold.get(key) != 0:
        raise SystemExit(f"runtime hold zero limit violated: {key}")

for key in (
    "actual_model_provider_call_enabled",
    "public_network_access_enabled",
    "external_network_egress_enabled",
    "dns_resolution_enabled",
    "provider_credential_read_enabled",
    "provider_token_read_enabled",
    "persistent_memory_write_enabled",
    "external_tool_execution_enabled",
    "external_connector_execution_enabled",
    "autonomous_background_loop_enabled",
    "production_runtime_authorized",
):
    if program["prohibited_capabilities"].get(key) is not False:
        raise SystemExit(f"runtime hold prohibited flag enabled: {key}")
PY

./scripts/adaptive-intelligence-program-authorization-check.sh
./scripts/adaptive-intelligence-program-authorization-no-go-regression.sh

if is_nested_gate_context; then
  echo "PASS: full repository check deferred to outer gate"
else
  (
    unset AION_BRAIN_PYTHON
    AION_AGGREGATE_GATE_RUNNING=1 ./scripts/check.sh
  )
fi

echo "adaptive intelligence runtime hold PASS"
