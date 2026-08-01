#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_BRAIN_PYTHON="$PYTHON_BIN"

./scripts/v02-staging-qualification-authorization-no-go-regression.sh >/dev/null

PYTHONPATH="$ROOT_DIR/scripts/lib:$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

import v02_release_qualification_foundation_operator_evaluation as h

root = Path.cwd()
program = json.loads((root / "docs/v02-release-qualification/program-ledger.json").read_text(encoding="utf-8"))
auth = json.loads((root / "docs/v02-release-qualification/authorization-ledger.json").read_text(encoding="utf-8"))
staging = json.loads((root / "examples/v02-release-qualification/staging-qualification-authorization.json").read_text(encoding="utf-8"))
report = json.loads((root / "examples/v02-release-qualification/foundation-operator-evaluation-report.json").read_text(encoding="utf-8"))
h.validate_report(report)

if report["decision"] != h.PASS_DECISION:
    raise SystemExit("AION-240 staging authorization requires exact PASS decision")
closed = program.get("aion_238_authorization_closeout", {})
if closed.get("authorization_transaction_id") != h.CURRENT_AUTHORIZATION_ID:
    raise SystemExit("AION-238 closeout record missing")
if closed.get("authorization_active") is not False or closed.get("authorization_consumed") is not True:
    raise SystemExit("AION-238 must be closed and consumed")
if closed.get("authorization_expired") is not True or closed.get("authorization_reusable") is not False:
    raise SystemExit("AION-238 must be expired and non-reusable")

required = {
    "program_id": h.PROGRAM_ID,
    "authorization_transaction_id": h.NEXT_AUTHORIZATION_ID,
    "approval_record_id": h.NEXT_AUTHORIZATION_ID,
    "parent_authorization_transaction_id": h.CURRENT_AUTHORIZATION_ID,
    "parent_evaluation_id": h.EVALUATION_ID,
    "parent_evaluation_decision": h.PASS_DECISION,
    "parent_implementation_task": h.IMPLEMENTATION_TASK,
    "parent_implementation_prs": [h.IMPLEMENTATION_PR],
    "parent_implementation_feature_commits": [h.IMPLEMENTATION_COMMIT, h.CI_FIX_COMMIT],
    "parent_implementation_merge_commits": [h.IMPLEMENTATION_MERGE_COMMIT],
    "parent_implementation_main_commit": h.IMPLEMENTATION_MERGE_COMMIT,
    "candidate_id": "controlled-isolated-local-staging-artifact-and-rollback-drill-core",
    "workstream": "v02-controlled-staging-qualification",
    "implementation_task": h.NEXT_IMPLEMENTATION_TASK,
    "formal_closeout_task": h.NEXT_FORMAL_CLOSEOUT_TASK,
    "final_planned_task": h.FINAL_PLANNED_TASK,
    "authorization_scope": h.STAGING_AUTHORIZATION_SCOPE,
    "authorization_transaction_approved": True,
    "explicit_approval_record_approval": True,
    "implementation_authorization_approved": True,
    "implementation_go_status": True,
    "implementation_no_go_status": False,
    "authorization_active": True,
    "authorization_consumed": False,
    "authorization_expired": False,
    "authorization_reusable": False,
}
for payload_name, payload in (("authorization ledger", auth), ("staging example", staging)):
    for key, expected in required.items():
        if payload.get(key) != expected:
            raise SystemExit(f"{payload_name} mismatch {key}: {payload.get(key)!r}")
    approved = payload.get("approved_capabilities", {})
    if not all(approved.get(key) is True for key in h.APPROVED_AION241_CAPABILITIES):
        raise SystemExit(f"{payload_name} approved capabilities mismatch")
    prohibited = payload.get("prohibited_capabilities", {})
    if not all(prohibited.get(key) is False for key in h.PROHIBITED_AION241_CAPABILITIES):
        raise SystemExit(f"{payload_name} prohibited capabilities mismatch")
    limits = payload.get("resource_limits", {})
    if {key: limits.get(key) for key in h.POSITIVE_AION241_LIMITS} != h.POSITIVE_AION241_LIMITS:
        raise SystemExit(f"{payload_name} positive resource limits mismatch")
    if any(limits.get(key) != 0 for key in h.ZERO_AION241_LIMITS):
        raise SystemExit(f"{payload_name} zero resource limits mismatch")

if program.get("active_v02_release_qualification_authorization_count") != 1:
    raise SystemExit("active v0.2 qualification authorization count mismatch")
if program.get("active_v02_release_qualification_authorization") != h.NEXT_AUTHORIZATION_ID:
    raise SystemExit("active v0.2 qualification authorization mismatch")
if program.get("active_v02_release_qualification_task") != h.NEXT_IMPLEMENTATION_TASK:
    raise SystemExit("active v0.2 qualification task mismatch")
if program.get("formal_closeout_task") != h.NEXT_FORMAL_CLOSEOUT_TASK:
    raise SystemExit("formal closeout task mismatch")
for future in h.FUTURE_AION241_SOURCE_SCOPE:
    if (root / future).exists():
        raise SystemExit(f"AION-241 source exists before implementation: {future}")
if (root / "scripts/v02-staging-qualification-local-run.py").exists():
    raise SystemExit("AION-241 runner exists before implementation")
for flag in (
    "controlled_staging_qualification_implemented",
    "production_runtime_authorized",
    "production_deployment_enabled",
    "release_candidate_creation_enabled",
    "v02_release_ready",
    "v02_tag_created",
    "v02_release_created",
):
    if program.get(flag) is not False:
        raise SystemExit(f"program must keep {flag}=false")
PY

aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | rg -n '.+'; then
  echo "ERROR: v0.2 tag exists" >&2
  exit 1
fi
if command -v gh >/dev/null 2>&1; then
  if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
    echo "ERROR: v0.2 release exists" >&2
    exit 1
  fi
fi

echo "controlled isolated staging qualification authorization PASS"
