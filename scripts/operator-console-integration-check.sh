#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_BRAIN_PYTHON="$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

./scripts/operator-console-integration-no-go-regression.sh
./scripts/operator-console-integrated-pilot-evidence-check.sh
AION_OPERATOR_CONSOLE_INTEGRATION_RUNTIME_HOLD_SKIP_FULL_CHECK=1 \
  ./scripts/operator-console-integration-runtime-hold.sh

"$PYTHON_BIN" -m pytest \
  services/brain-api/tests/test_operator_console_integration_authorization.py \
  services/brain-api/tests/test_operator_console_integration_authorized_capabilities.py \
  services/brain-api/tests/test_operator_console_integration_prohibited_capabilities.py \
  services/brain-api/tests/test_operator_console_integration_resource_budgets.py \
  services/brain-api/tests/test_operator_console_integration_route_manifest.py \
  services/brain-api/tests/test_operator_console_integration_security_headers.py \
  services/brain-api/tests/test_operator_console_integration_source_scope_spec.py \
  services/brain-api/tests/test_operator_console_integrated_local_runtime_aion237.py \
  services/brain-api/tests/test_operator_console_integrated_pilot_evidence_aion237.py \
  -q

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

root = Path(os.environ["AION_REPO_ROOT"])
auth = json.loads(
    (root / "examples/secure-runtime-integration/operator-console-integration-authorization.json")
    .read_text(encoding="utf-8")
)
program = json.loads(
    (root / "docs/secure-runtime-integration/program-ledger.json").read_text(encoding="utf-8")
)
pilot = json.loads(
    (
        root
        / "examples/secure-runtime-integration/operator-console-integrated-local-runtime-pilot-evidence.json"
    ).read_text(encoding="utf-8")
)
if auth["operator_console_integration_implemented"] is not True:
    raise SystemExit("implementation flag mismatch")
if auth["integrated_authenticated_local_pilot_completed"] is not True:
    raise SystemExit("pilot completion flag mismatch")
if program["program_state"] == "secure_runtime_integration_program_complete":
    if program["active_sri_implementation_authorization"] is not None:
        raise SystemExit("closed program active authorization mismatch")
    if program["active_sri_implementation_authorization_count"] != 0:
        raise SystemExit("closed program active authorization count mismatch")
    if program["formal_closeout_task"] is not None:
        raise SystemExit("closed program formal closeout mismatch")
    if program.get("final_completed_task") != "AION-238":
        raise SystemExit("closed program final task mismatch")
else:
    if program["active_sri_implementation_authorization"] != "AION-236-SRI-0004":
        raise SystemExit("active authorization mismatch")
    if program["formal_closeout_task"] != "AION-238":
        raise SystemExit("formal closeout mismatch")
if pilot["listener_closed"] is not True:
    raise SystemExit("pilot listener did not close")
if pilot["all_prohibited_effect_counters_zero"] is not True:
    raise SystemExit("pilot prohibited counters are not zero")
for key in (
    "public_listener_enabled",
    "external_network_egress_enabled",
    "browser_persistence_enabled",
    "production_runtime_authorized",
    "production_exposure",
    "v02_release_ready",
):
    if program[key] is not False:
        raise SystemExit(f"program boundary mismatch: {key}")
PY

echo "controlled operator console integration PASS"
