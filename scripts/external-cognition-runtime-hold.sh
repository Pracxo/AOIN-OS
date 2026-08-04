#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_EXTERNAL_COGNITION_RUNTIME_HOLD_SKIP_FULL_CHECK:-}" == "1" ]] && return 0
  [[ "${AION_EXTERNAL_COGNITION_RUNTIME_HOLD_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

nested_gate_context=0
if is_nested_gate_context; then
  nested_gate_context=1
fi
export AION_EXTERNAL_COGNITION_RUNTIME_HOLD_RUNNING=1

./scripts/external-cognition-foundation-check.sh
./scripts/adaptive-intelligence-program-authorization-check.sh
./scripts/adaptive-intelligence-program-authorization-no-go-regression.sh

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
hold = json.loads((ROOT / "examples/adaptive-intelligence/external-cognition-runtime-hold.json").read_text())

required = {
    "program_id": "AION-ADAPTIVE-INTELLIGENCE-001",
    "adaptive_intelligence_program_authorized": True,
    "adaptive_intelligence_program_implemented": False,
    "external_cognition_gateway_implemented": True,
    "production_runtime_authorized": False,
}
program_states = {
    "external_cognition_gateway_foundation_implemented_disabled_pending_AION-247_closeout",
    "external_cognition_foundation_evaluated_live_provider_pilot_authorized_not_implemented",
}
gateway_states = {
    "implemented_disabled_deterministic_fixture_only_pending_AION-247_closeout",
    "implemented_disabled_deterministic_fixture_only_operator_evaluated_live_provider_pilot_authorized_not_implemented",
}
for key, value in required.items():
    if program.get(key) != value and hold.get(key) != value:
        raise SystemExit(f"external cognition runtime hold mismatch {key}")
if program.get("program_state") not in program_states:
    raise SystemExit("external cognition runtime hold program state mismatch")
if program.get("external_cognition_gateway_state") not in gateway_states:
    raise SystemExit("external cognition runtime hold gateway state mismatch")
if program.get("program_state") == "external_cognition_foundation_evaluated_live_provider_pilot_authorized_not_implemented":
    lineage = {
        "active_adaptive_intelligence_authorization": "AION-247-AI-0002",
        "active_adaptive_intelligence_task": "AION-248",
        "formal_closeout_task": "AION-249",
    }
else:
    lineage = {
        "active_adaptive_intelligence_authorization": "AION-245-AI-0001",
        "active_adaptive_intelligence_task": "AION-246",
        "formal_closeout_task": "AION-247",
    }
for key, value in lineage.items():
    if program.get(key) != value and hold.get(key) != value:
        raise SystemExit(f"external cognition runtime hold lineage mismatch {key}")

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
        raise SystemExit(f"external cognition runtime hold zero limit violated: {key}")

for key in (
    "actual_model_provider_call_enabled",
    "provider_network_adapter_enabled",
    "public_network_access_enabled",
    "external_network_egress_enabled",
    "dns_resolution_enabled",
    "provider_credential_read_enabled",
    "provider_token_read_enabled",
    "provider_authorization_header_creation_enabled",
    "raw_prompt_persistence_enabled",
    "raw_response_persistence_enabled",
    "persistent_memory_write_enabled",
    "external_tool_execution_enabled",
    "external_connector_execution_enabled",
    "autonomous_background_loop_enabled",
    "production_runtime_authorized",
):
    if program["prohibited_capabilities"].get(key) is not False:
        raise SystemExit(f"external cognition runtime hold prohibited flag enabled: {key}")
PY

if [[ "$nested_gate_context" == "1" ]]; then
  echo "PASS: full repository check deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/check.sh
fi

echo "external cognition gateway runtime hold PASS"
