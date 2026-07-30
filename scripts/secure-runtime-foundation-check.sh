#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

./scripts/secure-runtime-foundation-no-go-regression.sh
./scripts/secure-runtime-foundation-pilot-evidence-check.sh
"$PYTHON_BIN" -m pytest services/brain-api/tests/test_secure_runtime_*.py -q

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

from aion_brain.contracts.secure_runtime import (
    AUTHORIZATION_TRANSACTION_ID,
    CLOSED_CAPABILITY_CODES,
    PROGRAM_ID,
    SecureRuntimeMode,
)

root = Path(os.environ["AION_REPO_ROOT"])
program = json.loads((root / "docs/secure-runtime-integration/program-ledger.json").read_text())
auth = json.loads((root / "docs/secure-runtime-integration/authorization-ledger.json").read_text())
pilot = json.loads((root / "examples/secure-runtime-integration/local-operator-runtime-pilot-evidence.json").read_text())

assert PROGRAM_ID == "AION-SECURE-RUNTIME-INTEGRATION-001"
assert AUTHORIZATION_TRANSACTION_ID == "AION-230-SRI-0001"
assert SecureRuntimeMode.operator_invoked_local.value == "operator_invoked_local"
assert CLOSED_CAPABILITY_CODES == (
    "brain.think.simulate",
    "secure_runtime.audit.read",
    "secure_runtime.fixture.replay",
    "secure_runtime.health.read",
    "secure_runtime.observability.read",
)
for payload in (program, auth):
    assert payload["secure_runtime_foundation_implemented"] is True
    assert payload["secure_runtime_implemented"] is True
    assert payload["local_operator_runtime_available"] is True
    if "authorization_active" in payload:
        assert payload["authorization_active"] is True
        assert payload["authorization_consumed"] is False
        assert payload["authorization_expired"] is False
        assert payload["authorization_reusable"] is False
    assert payload["production_auth_runtime_enabled"] is False
    assert payload["public_auth_endpoint_enabled"] is False
    assert payload["credential_persistence_enabled"] is False
    assert payload["token_persistence_enabled"] is False
    assert payload["model_provider_call_enabled"] is False
    assert payload["connector_execution_enabled"] is False
    assert payload["actual_tool_execution_enabled"] is False
    assert payload["module_activation_enabled"] is False
    assert payload["production_write_execution_enabled"] is False
    assert payload["glm_live_execution_enabled"] is False
    assert payload["source_rewrite_enabled"] is False
    assert payload["git_mutation_enabled"] is False
    assert payload["production_deployment_enabled"] is False
    assert payload["model_weight_training_enabled"] is False
    assert payload["production_exposure"] is False
    assert payload["v02_release_ready"] is False
assert pilot["simulated_dispatches"] == 1
assert pilot["stage_receipts"] >= 1
assert pilot["audit_records"] >= 1
PY

echo "secure runtime foundation PASS"
