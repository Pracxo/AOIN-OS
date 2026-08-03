#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_BRAIN_PYTHON="$PYTHON_BIN"

AION_243_IMPLEMENTATION_CONTEXT=1 \
./scripts/v02-release-candidate-authorization-no-go-regression.sh >/dev/null

PYTHONPATH="$ROOT_DIR/scripts/lib:$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

from aion_brain.contracts import v02_release_candidate as c
import v02_staging_qualification_operator_evaluation as ev

root = Path.cwd()
report = json.loads((root / "examples/v02-release-qualification/staging-qualification-operator-evaluation-report.json").read_text(encoding="utf-8"))
program = json.loads((root / "docs/v02-release-qualification/program-ledger.json").read_text(encoding="utf-8"))
auth = json.loads((root / "docs/v02-release-qualification/authorization-ledger.json").read_text(encoding="utf-8"))
candidate = json.loads((root / "examples/v02-release-qualification/release-candidate-authorization.json").read_text(encoding="utf-8"))

ev.validate_report(report)
expected_approved = dict.fromkeys(ev.APPROVED_AION243_CAPABILITIES, True)
expected_prohibited = dict.fromkeys(ev.PROHIBITED_AION243_CAPABILITIES, False)
expected_limits = {**ev.POSITIVE_AION243_LIMITS, **dict.fromkeys(ev.ZERO_AION243_LIMITS, 0)}

for label, payload in (("program", program), ("authorization", auth), ("candidate", candidate)):
    if payload.get("active_v02_release_qualification_authorization") == "AION-244-V02REL-0001":
        publication_auth = payload.get("aion_244_publication_authorization", {})
        if publication_auth.get("authorization_transaction_id") != "AION-244-V02REL-0001":
            raise SystemExit(f"{label} missing AION-244 publication authorization")
        if publication_auth.get("authorization_active") is not True:
            raise SystemExit(f"{label} AION-244 publication authorization must be active")
        if publication_auth.get("authorization_consumed") is not False:
            raise SystemExit(f"{label} AION-244 publication authorization must be unconsumed")
        if payload.get("release_candidate_published") is not False:
            raise SystemExit(f"{label} release candidate must remain unpublished before AION-244 publication")
        continue
    required = {
        "controlled_staging_qualification_operator_evaluation_passed": True,
        "controlled_staging_qualification_operator_evaluation_id": ev.EVALUATION_ID,
        "controlled_staging_qualification_operator_evaluation_decision": ev.PASS_DECISION,
        "authorization_transaction_id": ev.NEXT_AUTHORIZATION_ID,
        "approval_record_id": ev.NEXT_AUTHORIZATION_ID,
        "parent_authorization_transaction_id": ev.CURRENT_AUTHORIZATION_ID,
        "parent_evaluation_id": ev.EVALUATION_ID,
        "parent_evaluation_decision": ev.PASS_DECISION,
        "implementation_task": ev.NEXT_IMPLEMENTATION_TASK,
        "formal_closeout_task": ev.NEXT_FORMAL_CLOSEOUT_TASK,
        "final_planned_task": ev.FINAL_PLANNED_TASK,
        "authorization_active": True,
        "authorization_consumed": False,
        "authorization_expired": False,
        "authorization_reusable": False,
        "active_v02_release_qualification_authorization_count": 1,
        "active_v02_release_qualification_authorization": ev.NEXT_AUTHORIZATION_ID,
        "active_v02_release_qualification_task": ev.NEXT_IMPLEMENTATION_TASK,
        "release_candidate_artifact_build_authorized": True,
        "release_candidate_creation_enabled": True,
        "release_candidate_published": False,
        "production_runtime_authorized": False,
        "production_deployment_enabled": False,
        "v02_release_ready": False,
        "v02_tag_created": False,
        "v02_release_created": False,
    }
    evidence_exists = (
        root
        / "examples/v02-release-qualification/v02-release-candidate-artifact-build-evidence.json"
    ).is_file()
    if evidence_exists:
        required.update(
            {
                "release_candidate_artifact_build_implemented": True,
                "release_candidate_artifact_state": (
                    "implemented_local_candidate_retained_pending_AION-244_closeout"
                ),
                "release_candidate_created": True,
                "candidate_bundle_retained": True,
                "candidate_local_image_retained": True,
            }
        )
    else:
        required.update(
            {
                "release_candidate_artifact_build_implemented": False,
                "release_candidate_artifact_state": "authorized_not_implemented",
                "release_candidate_created": False,
            }
        )
    for key, expected in required.items():
        if payload.get(key) != expected:
            raise SystemExit(f"{label} release-candidate authorization mismatch {key}: {payload.get(key)!r}")
    expected_contract_approved = dict.fromkeys(c.APPROVED_CAPABILITIES, True)
    expected_contract_prohibited = dict.fromkeys(c.PROHIBITED_CAPABILITIES, False)
    expected_contract_limits = {**c.POSITIVE_RESOURCE_LIMITS, **dict.fromkeys(c.ZERO_RESOURCE_LIMITS, 0)}
    if payload.get("approved_capabilities") not in (expected_approved, expected_contract_approved):
        raise SystemExit(f"{label} approved capabilities mismatch")
    if payload.get("prohibited_capabilities") not in (expected_prohibited, expected_contract_prohibited):
        raise SystemExit(f"{label} prohibited capabilities mismatch")
    if payload.get("resource_limits") not in (expected_limits, expected_contract_limits):
        raise SystemExit(f"{label} resource limits mismatch")

closeout = program.get("aion_240_authorization_closeout", {})
if closeout.get("authorization_transaction_id") != ev.CURRENT_AUTHORIZATION_ID:
    raise SystemExit("missing AION-240 closeout")
if closeout.get("authorization_active") is not False or closeout.get("authorization_consumed") is not True:
    raise SystemExit("AION-240 closeout state mismatch")
if closeout.get("authorization_expired") is not True or closeout.get("authorization_reusable") is not False:
    raise SystemExit("AION-240 closeout expiry/reuse mismatch")
for relative in c.REQUIRED_SOURCE_SCOPE:
    if not (root / relative).is_file():
        raise SystemExit(f"AION-243 authorized source is missing: {relative}")
PY

echo "deterministic v0.2 release candidate artifact build authorization PASS"
