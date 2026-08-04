#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

./scripts/live-provider-pilot-authorization-no-go-regression.sh

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
HARNESS = ROOT / "scripts/lib/external_cognition_foundation_operator_evaluation.py"
REPORT = (
    ROOT
    / "examples/adaptive-intelligence/external-cognition-foundation-operator-evaluation-report.json"
)
AUTH_LEDGER = ROOT / "docs/adaptive-intelligence/authorization-ledger.json"

spec = importlib.util.spec_from_file_location("aion247_external_cognition_eval", HARNESS)
if spec is None or spec.loader is None:
    raise SystemExit("cannot load AION-247 evaluation harness")
harness = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = harness
spec.loader.exec_module(harness)

if not REPORT.exists():
    print("PASS: live-provider pilot authorization remains pending immutable evaluation")
    raise SystemExit(0)

payload = json.loads(REPORT.read_text(encoding="utf-8"))
harness.validate_evaluation_report(payload)
if payload["decision"] != harness.PASS_DECISION:
    raise SystemExit("live-provider pilot authorization requires exact AION-247 PASS decision")

ledger = json.loads(AUTH_LEDGER.read_text(encoding="utf-8"))
records = {
    record.get("authorization_transaction_id"): record for record in ledger.get("records", [])
}
current = records.get("AION-245-AI-0001")
successor = records.get("AION-247-AI-0002")
if current is None or successor is None:
    raise SystemExit("AION-245 closeout or AION-247 successor authorization missing")
if current.get("authorization_active") is not False:
    raise SystemExit("AION-245-AI-0001 must be inactive")
if current.get("authorization_consumed") is not True:
    raise SystemExit("AION-245-AI-0001 must be consumed")
if current.get("authorization_expired") is not True:
    raise SystemExit("AION-245-AI-0001 must be expired")
if current.get("authorization_reusable") is not False:
    raise SystemExit("AION-245-AI-0001 must remain non-reusable")
required_successor = {
    "authorization_active": True,
    "authorization_consumed": False,
    "authorization_expired": False,
    "authorization_reusable": False,
    "implementation_task": "AION-248",
    "formal_closeout_task": "AION-249",
    "provider_id": "openai",
    "provider_api_family": "responses",
    "allowed_endpoint_host": "api.openai.com",
    "allowed_endpoint_path": "/v1/responses",
    "maximum_selected_models": 1,
}
for key, expected in required_successor.items():
    if successor.get(key) != expected:
        raise SystemExit(f"AION-247-AI-0002 field mismatch {key}")
if ledger.get("active_adaptive_intelligence_authorization_count") != 1:
    raise SystemExit("there must be exactly one active Adaptive Intelligence authorization")
if ledger.get("active_adaptive_intelligence_authorization") != "AION-247-AI-0002":
    raise SystemExit("AION-247-AI-0002 must be the active authorization")

print("live provider pilot authorization PASS")
PY
