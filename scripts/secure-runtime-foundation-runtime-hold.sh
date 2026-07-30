#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_SECURE_RUNTIME_FOUNDATION_SKIP_FULL_CHECK:-}" == "1" ]] && return 0
  [[ "${AION_SECURE_RUNTIME_FOUNDATION_RUNTIME_HOLD_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

nested_gate_context=0
if is_nested_gate_context; then
  nested_gate_context=1
fi

export AION_SECURE_RUNTIME_FOUNDATION_RUNTIME_HOLD_RUNNING=1
./scripts/secure-runtime-foundation-check.sh

python3 - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

ledger = json.loads(Path("docs/secure-runtime-integration/program-ledger.json").read_text())
required_false = (
    "production_auth_runtime_enabled",
    "public_auth_endpoint_enabled",
    "credential_persistence_enabled",
    "token_persistence_enabled",
    "general_network_access_enabled",
    "model_provider_call_enabled",
    "connector_execution_enabled",
    "actual_tool_execution_enabled",
    "module_activation_enabled",
    "production_write_execution_enabled",
    "glm_live_execution_enabled",
    "source_rewrite_enabled",
    "production_deployment_enabled",
    "model_weight_training_enabled",
    "production_exposure",
)
assert ledger["local_operator_runtime_available"] is True
for key in required_false:
    assert ledger[key] is False, key
PY

if [[ "$nested_gate_context" == "1" ]]; then
  echo "PASS: full repository check deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/check.sh
fi

aion_confirm_immutable_v01_tag_history >/dev/null

echo "secure runtime foundation runtime hold PASS"
