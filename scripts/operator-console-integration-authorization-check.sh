#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_BRAIN_PYTHON="$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

./scripts/operator-console-integration-authorization-no-go-regression.sh

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

root = Path(os.environ["AION_REPO_ROOT"])
auth = json.loads((root / "examples/secure-runtime-integration/operator-console-integration-authorization.json").read_text())
program = json.loads((root / "docs/secure-runtime-integration/program-ledger.json").read_text())
ledger = json.loads((root / "docs/secure-runtime-integration/authorization-ledger.json").read_text())
route = json.loads((root / "examples/secure-runtime-integration/operator-console-route-manifest.json").read_text())
expected = "AION-236-SRI-0004"
if auth["authorization_transaction_id"] != expected or ledger["authorization_transaction_id"] != expected:
    raise SystemExit("authorization id mismatch")
if program["active_sri_implementation_authorization"] != expected:
    raise SystemExit("active SRI authorization mismatch")
if program["active_sri_implementation_task"] != "AION-237":
    raise SystemExit("active SRI task mismatch")
if auth["parent_authorization_transaction_id"] != "AION-234-SRI-0003":
    raise SystemExit("parent authorization mismatch")
if auth["parent_evaluation_decision"] != "SANDBOXED_DETERMINISTIC_CAPABILITY_RUNTIME_OPERATOR_EVALUATION_PASS_RECOMMEND_CONTROLLED_OPERATOR_CONSOLE_INTEGRATED_LOCAL_RUNTIME_AUTHORIZATION":
    raise SystemExit("evaluation decision mismatch")
if auth["implementation_task"] != "AION-237" or auth["formal_closeout_task"] != "AION-238":
    raise SystemExit("task lineage mismatch")
if len(route["routes"]) != 10 or route["routes"] != auth["route_manifest"]:
    raise SystemExit("route manifest mismatch")
if not all(auth["operator_console_authorized_capabilities"].values()):
    raise SystemExit("authorized capability false")
if any(auth["operator_console_prohibited_capabilities"].values()):
    raise SystemExit("prohibited capability true")
if auth["operator_console_resource_limits"]["maximum_routes"] != 10:
    raise SystemExit("route limit mismatch")
if any((root / item).exists() for item in auth["future_source_scope"]):
    raise SystemExit("AION-237 source exists too early")
for key in (
    "public_listener_enabled",
    "external_network_egress_enabled",
    "browser_cookie_persistence_enabled",
    "browser_local_storage_enabled",
    "browser_session_storage_enabled",
    "browser_indexeddb_enabled",
    "production_runtime_authorized",
    "v02_release_ready",
):
    if auth["operator_console_prohibited_capabilities"][key] is not False:
        raise SystemExit(f"prohibited flag mismatch: {key}")
closed = program["aion_234_record"]
if closed["authorization_state"] != "consumed_by_AION-235_closed_by_AION-236":
    raise SystemExit("AION-234 closeout mismatch")
PY

echo "controlled operator console integration authorization PASS"
