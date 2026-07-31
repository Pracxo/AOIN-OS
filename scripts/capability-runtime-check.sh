#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_BRAIN_PYTHON="$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

./scripts/capability-runtime-no-go-regression.sh
./scripts/capability-runtime-pilot-evidence-check.sh
"$PYTHON_BIN" -m pytest \
  services/brain-api/tests/test_capability_runtime_contracts_aion235.py \
  services/brain-api/tests/test_capability_runtime_manifests_aion235.py \
  services/brain-api/tests/test_capability_runtime_schema_validation_aion235.py \
  services/brain-api/tests/test_capability_runtime_dispatcher_aion235.py \
  services/brain-api/tests/test_capability_runtime_replay_and_guards_aion235.py \
  services/brain-api/tests/test_capability_runtime_pilot_evidence_aion235.py \
  services/brain-api/tests/test_capability_runtime_no_runtime_effects_aion235.py \
  services/brain-api/tests/test_capability_runtime_current_state_after_aion235.py \
  services/brain-api/tests/test_secure_runtime_current_state_after_aion234.py \
  -q

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

from aion_brain.contracts.sandboxed_capability_runtime import (
    ALL_RESOURCE_LIMITS,
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_TRANSACTION_ID,
    AUTHORIZED_CAPABILITY_FLAGS,
    PROHIBITED_CAPABILITY_FLAGS,
)

ROOT = Path(os.environ["AION_REPO_ROOT"])
program = json.loads((ROOT / "docs/secure-runtime-integration/program-ledger.json").read_text(encoding="utf-8"))
auth = json.loads((ROOT / "docs/secure-runtime-integration/authorization-ledger.json").read_text(encoding="utf-8"))
example = json.loads((ROOT / "examples/secure-runtime-integration/capability-runtime-authorization.json").read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


for payload in (program, auth, example):
    require(payload["authorization_transaction_id"] == AUTHORIZATION_TRANSACTION_ID, "authorization id mismatch")
    require(payload["authorization_scope"] == AUTHORIZATION_SCOPE, "authorization scope mismatch")
    require(payload["authorization_active"] is True, "authorization inactive")
    require(payload["authorization_consumed"] is False, "authorization consumed")
    require(payload["authorization_expired"] is False, "authorization expired")
    require(payload["authorization_reusable"] is False, "authorization reusable")
    require(payload["active_sri_implementation_authorization_count"] == 1, "active SRI auth count mismatch")
    require(payload["active_sri_implementation_authorization"] == AUTHORIZATION_TRANSACTION_ID, "active SRI auth mismatch")
    require(payload["active_sri_implementation_task"] == "AION-235", "active task mismatch")
    require(payload["formal_closeout_task"] == "AION-236", "formal closeout mismatch")
    require(payload["sandboxed_capability_runtime_implemented"] is True or payload["capability_runtime_implemented"] is True, "runtime not implemented")
    authorized = payload.get("capability_runtime_authorized_capabilities") or payload.get("authorized_capabilities")
    prohibited = payload.get("capability_runtime_prohibited_capabilities") or payload.get("prohibited_capabilities")
    limits = payload.get("capability_runtime_resource_limits") or payload.get("resource_limits")
    require(set(authorized) == set(AUTHORIZED_CAPABILITY_FLAGS), "authorized flag set mismatch")
    require(all(authorized[key] is True for key in AUTHORIZED_CAPABILITY_FLAGS), "authorized flag false")
    require(set(prohibited) == set(PROHIBITED_CAPABILITY_FLAGS), "prohibited flag set mismatch")
    require(all(prohibited[key] is False for key in PROHIBITED_CAPABILITY_FLAGS), "prohibited flag true")
    require(limits == ALL_RESOURCE_LIMITS, "resource limit mismatch")

record = program["aion_234_record"]
require(record["pull_requests"] == [153], "AION-234 PR not reconciled")
require(record["merge_commits"] == ["74c6ecc93333518a353bd4c69ad8823d7a47afd8"], "AION-234 merge commit not reconciled")
require(program["aion_235_record"]["runtime_state"] == "sandboxed_capability_runtime_implemented_reference_only_pending_closeout", "AION-235 record mismatch")
PY

echo "sandboxed capability runtime PASS"
