#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

./scripts/capability-runtime-no-go-regression.sh
"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
for relative in (
    "docs/secure-runtime-integration/program-ledger.json",
    "docs/secure-runtime-integration/authorization-ledger.json",
    "examples/secure-runtime-integration/capability-runtime-authorization.json",
):
    payload = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    prohibited = payload.get("capability_runtime_prohibited_capabilities") or payload.get("prohibited_capabilities", {})
    for key, value in prohibited.items():
        if value is not False:
            raise SystemExit(f"prohibited capability flag is not false in {relative}: {key}")
    if payload.get("authorization_transaction_id") == "AION-234-SRI-0003":
        if payload.get("authorization_active") is not True:
            raise SystemExit(f"authorization inactive in {relative}")
        if payload.get("authorization_consumed") is not False:
            raise SystemExit(f"authorization consumed in {relative}")
        if payload.get("authorization_expired") is not False:
            raise SystemExit(f"authorization expired in {relative}")
        if payload.get("authorization_reusable") is not False:
            raise SystemExit(f"authorization reusable in {relative}")
        continue

    active_sri = payload.get("active_sri_implementation_authorization")
    completed_sri = (
        payload.get("program_state") == "secure_runtime_integration_program_complete"
        and payload.get("active_sri_implementation_authorization_count") == 0
        and active_sri is None
        and payload.get("final_completed_task") == "AION-238"
    )
    if active_sri != "AION-236-SRI-0004" and not completed_sri:
        raise SystemExit(f"authorization id mismatch in {relative}")

    if relative == "docs/secure-runtime-integration/program-ledger.json":
        closed = payload.get("aion_234_record", {})
        if closed.get("authorization_transaction") != "AION-234-SRI-0003":
            raise SystemExit(f"AION-234 closeout record missing in {relative}")
    else:
        closed = next(
            (
                item
                for item in payload.get("records", [])
                if item.get("authorization_transaction_id") == "AION-234-SRI-0003"
            ),
            None,
        )
        if not closed:
            raise SystemExit(f"AION-234 closeout record missing in {relative}")
    if closed.get("authorization_active") is not False:
        raise SystemExit(f"closed authorization active in {relative}")
    if closed.get("authorization_consumed") is not True:
        raise SystemExit(f"closed authorization not consumed in {relative}")
    if closed.get("authorization_expired") is not True:
        raise SystemExit(f"closed authorization not expired in {relative}")
    if closed.get("authorization_reusable") is not False:
        raise SystemExit(f"closed authorization reusable in {relative}")
    if closed.get("authorization_consumed_by_task") != "AION-235":
        raise SystemExit(f"closed authorization consumer mismatch in {relative}")
    if closed.get("authorization_closed_by_task") != "AION-236":
        raise SystemExit(f"closed authorization closeout mismatch in {relative}")
PY

aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | grep -q .; then
  echo "ERROR: v0.2 tag exists" >&2
  exit 1
fi

echo "sandboxed capability runtime authorization no-go PASS"
