#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_MODEL_GATEWAY_RUNTIME_HOLD_SKIP_FULL_CHECK:-}" == "1" ]] && return 0
  [[ "${AION_MODEL_GATEWAY_RUNTIME_HOLD_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}
nested_gate_context=0
if is_nested_gate_context; then nested_gate_context=1; fi
export AION_MODEL_GATEWAY_RUNTIME_HOLD_RUNNING=1
./scripts/model-gateway-check.sh
PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"
"$PYTHON_BIN" - <<'PY'
from __future__ import annotations
import json, os
from pathlib import Path
root = Path(os.environ["AION_REPO_ROOT"])
for payload in (json.loads((root / "docs/secure-runtime-integration/program-ledger.json").read_text()), json.loads((root / "docs/secure-runtime-integration/authorization-ledger.json").read_text())):
    if payload["model_gateway_implemented"] is not True:
        raise SystemExit("model gateway must remain implemented under runtime hold")
    if payload["model_gateway_state"] not in {
        "implemented_provider_neutral_reference_simulation_only_pending_AION-234_closeout",
        "implemented_provider_neutral_reference_simulation_only",
    }:
        raise SystemExit("model gateway state mismatch")
    if payload["deterministic_reference_provider_available"] is not True:
        raise SystemExit("reference provider must remain available")
    for key in ("actual_model_provider_call_enabled", "provider_network_egress_enabled", "provider_sdk_enabled", "provider_credential_read_enabled", "provider_credential_persistence_enabled", "api_key_persistence_enabled", "token_persistence_enabled", "authorization_header_creation_enabled", "live_model_session_enabled", "prompt_persistence_enabled", "model_response_persistence_enabled", "tool_calling_enabled", "function_calling_enabled", "connector_execution_enabled", "actual_tool_execution_enabled", "production_runtime_authorized", "production_memory_write_enabled", "production_policy_mutation_enabled", "actual_belief_creation_enabled", "actual_belief_mutation_enabled", "source_rewrite_enabled", "production_deployment_enabled", "model_weight_training_enabled", "production_exposure", "v02_release_ready"):
        assert payload[key] is False, key
PY
if [[ "$nested_gate_context" == "1" ]]; then
  echo "PASS: full repository check deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/check.sh
fi
echo "controlled model gateway runtime hold PASS"
