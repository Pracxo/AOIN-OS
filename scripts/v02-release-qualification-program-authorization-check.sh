#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

./scripts/v02-release-qualification-program-authorization-no-go-regression.sh

PYTHONPATH="$ROOT_DIR/scripts/lib:$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

from secure_runtime_integration_final_evaluation import (
    IMPLEMENTATION_FEATURE_COMMIT,
    IMPLEMENTATION_MERGE_COMMIT,
    IMPLEMENTATION_PR,
    PASS_DECISION,
    SUCCESSOR_AUTHORIZATION_ID,
    SUCCESSOR_CLOSEOUT_TASK,
    SUCCESSOR_IMPLEMENTATION_TASK,
    SUCCESSOR_PROGRAM_ID,
)
import v02_release_qualification_foundation_operator_evaluation as aion240

root = Path(os.environ["AION_REPO_ROOT"])
program = json.loads(
    (root / "docs/v02-release-qualification/program-ledger.json").read_text(
        encoding="utf-8"
    )
)
auth = json.loads(
    (root / "docs/v02-release-qualification/authorization-ledger.json").read_text(
        encoding="utf-8"
    )
)

if auth.get("authorization_transaction_id") == aion240.NEXT_AUTHORIZATION_ID:
    expected_program_state = (
        "v02_qualification_foundation_evaluated_controlled_staging_qualification_"
        "authorized_not_implemented"
    )
    aion241_final_state = (
        "controlled_isolated_staging_qualification_implemented_pilot_complete_"
        "pending_closeout"
    )
    aion241_controlled_state = "implemented_isolated_local_pilot_complete_pending_AION-242_closeout"
    for label, payload in (("program", program), ("authorization", auth)):
        if payload.get("program_state") not in {expected_program_state, aion241_final_state}:
            raise SystemExit(f"{label} post-closeout program_state mismatch")
        aion241_complete = payload.get("program_state") == aion241_final_state
        required = {
            "program_id": aion240.PROGRAM_ID,
            "v02_release_qualification_foundation_implemented": True,
            "v02_release_qualification_foundation_operator_evaluation_passed": True,
            "v02_release_qualification_foundation_operator_evaluation_id": aion240.EVALUATION_ID,
            "v02_release_qualification_foundation_operator_evaluation_decision": aion240.PASS_DECISION,
            "active_v02_release_qualification_authorization_count": 1,
            "active_v02_release_qualification_authorization": aion240.NEXT_AUTHORIZATION_ID,
            "active_v02_release_qualification_task": aion240.NEXT_IMPLEMENTATION_TASK,
            "formal_closeout_task": aion240.NEXT_FORMAL_CLOSEOUT_TASK,
            "controlled_staging_qualification_authorized": True,
            "controlled_staging_qualification_implemented": aion241_complete,
            "production_runtime_authorized": False,
            "production_deployment_enabled": False,
            "v02_release_candidate_created": False,
            "v02_release_ready": False,
            "v02_tag_created": False,
            "v02_release_created": False,
        }
        for key, expected in required.items():
            if payload.get(key) != expected:
                raise SystemExit(f"{label} post-closeout mismatch {key}: {payload.get(key)!r}")
        if aion241_complete:
            final_required = {
                "controlled_staging_qualification_state": aion241_controlled_state,
                "local_staging_pilot_completed": True,
                "offline_local_build_completed": True,
                "local_staging_artifact_created": True,
                "local_sbom_created": True,
                "local_provenance_created": True,
                "isolated_staging_deployment_completed": True,
                "staging_security_validation_completed": True,
                "staging_rollback_drill_completed": True,
                "staging_cleanup_completed": True,
                "active_staging_resources": 0,
            }
            for key, expected in final_required.items():
                if payload.get(key) != expected:
                    raise SystemExit(f"{label} AION-241 final mismatch {key}: {payload.get(key)!r}")
        closed = payload.get("aion_238_authorization_closeout", {})
        if closed.get("authorization_transaction_id") != aion240.CURRENT_AUTHORIZATION_ID:
            raise SystemExit(f"{label} missing AION-238 closeout")
        if closed.get("authorization_active") is not False:
            raise SystemExit(f"{label} AION-238 closeout active flag mismatch")
        if closed.get("authorization_consumed") is not True:
            raise SystemExit(f"{label} AION-238 closeout consumed flag mismatch")
        if closed.get("authorization_expired") is not True:
            raise SystemExit(f"{label} AION-238 closeout expired flag mismatch")
        if closed.get("authorization_reusable") is not False:
            raise SystemExit(f"{label} AION-238 closeout reusable flag mismatch")
        if payload.get("aion_239_record", {}).get("ci_result") != "pass":
            raise SystemExit(f"{label} AION-239 delivery reconciliation missing")
    required_auth = {
        "program_id": aion240.PROGRAM_ID,
        "authorization_transaction_id": aion240.NEXT_AUTHORIZATION_ID,
        "approval_record_id": aion240.NEXT_AUTHORIZATION_ID,
        "parent_authorization_transaction_id": aion240.CURRENT_AUTHORIZATION_ID,
        "parent_evaluation_id": aion240.EVALUATION_ID,
        "parent_evaluation_decision": aion240.PASS_DECISION,
        "parent_implementation_task": aion240.IMPLEMENTATION_TASK,
        "parent_implementation_prs": [aion240.IMPLEMENTATION_PR],
        "parent_implementation_feature_commits": [
            aion240.IMPLEMENTATION_COMMIT,
            aion240.CI_FIX_COMMIT,
        ],
        "parent_implementation_merge_commits": [aion240.IMPLEMENTATION_MERGE_COMMIT],
        "parent_implementation_main_commit": aion240.IMPLEMENTATION_MERGE_COMMIT,
        "candidate_id": "controlled-isolated-local-staging-artifact-and-rollback-drill-core",
        "workstream": "v02-controlled-staging-qualification",
        "implementation_task": aion240.NEXT_IMPLEMENTATION_TASK,
        "formal_closeout_task": aion240.NEXT_FORMAL_CLOSEOUT_TASK,
        "authorization_scope": aion240.STAGING_AUTHORIZATION_SCOPE,
        "authorization_active": True,
        "authorization_consumed": False,
        "authorization_expired": False,
        "authorization_reusable": False,
    }
    for key, expected in required_auth.items():
        if auth.get(key) != expected:
            raise SystemExit(f"authorization post-closeout mismatch {key}: {auth.get(key)!r}")
    raise SystemExit(0)

expected_scope = (
    "disabled-production-readiness-qualification-production-auth-composition-request-"
    "identity-replay-ledger-provisioning-idp-adapter-key-rotation-protected-material-"
    "credential-token-session-lifecycle-deployment-artifact-sbom-provenance-rollback-"
    "observability-threat-model-runtime-guard-release-gate-staging-plan-no-production-"
    "activation-no-release-core"
)
expected_program = {
    "program_id": SUCCESSOR_PROGRAM_ID,
    "program_name": "AION v0.2 Release Qualification Program",
    "created_by_task": "AION-238",
    "program_state": "v02_release_qualification_foundation_implemented_disabled_pending_closeout",
    "parent_evaluation_id": "AION-SRIPE-004",
    "parent_evaluation_decision": PASS_DECISION,
    "v02_release_qualification_program_authorized": True,
    "v02_release_qualification_program_implemented": True,
    "v02_release_qualification_foundation_authorized": True,
    "v02_release_qualification_foundation_implemented": True,
    "v02_release_qualification_foundation_state": (
        "implemented_disabled_design_and_local_simulation_pending_AION-240_closeout"
    ),
    "local_qualification_pilot_completed": True,
    "active_v02_release_qualification_authorization_count": 1,
    "active_v02_release_qualification_authorization": SUCCESSOR_AUTHORIZATION_ID,
    "active_v02_release_qualification_task": SUCCESSOR_IMPLEMENTATION_TASK,
    "formal_closeout_task": SUCCESSOR_CLOSEOUT_TASK,
    "final_planned_task": "AION-244",
    "production_runtime_authorized": False,
    "staging_runtime_authorized": False,
    "v02_release_candidate_created": False,
    "v02_release_ready": False,
    "v02_tag_created": False,
    "v02_release_created": False,
}
for label, payload in (("program", program), ("authorization", auth)):
    for key, expected in expected_program.items():
        if payload.get(key) != expected:
            raise SystemExit(f"{label} mismatch {key}: {payload.get(key)!r}")

required_auth = {
    "program_id": SUCCESSOR_PROGRAM_ID,
    "authorization_transaction_id": SUCCESSOR_AUTHORIZATION_ID,
    "approval_record_id": SUCCESSOR_AUTHORIZATION_ID,
    "parent_program_id": "AION-SECURE-RUNTIME-INTEGRATION-001",
    "parent_evaluation_id": "AION-SRIPE-004",
    "parent_evaluation_decision": PASS_DECISION,
    "parent_implementation_task": "AION-237",
    "parent_implementation_prs": [IMPLEMENTATION_PR],
    "parent_implementation_feature_commits": [IMPLEMENTATION_FEATURE_COMMIT],
    "parent_implementation_merge_commits": [IMPLEMENTATION_MERGE_COMMIT],
    "parent_implementation_main_commit": IMPLEMENTATION_MERGE_COMMIT,
    "candidate_id": "disabled-v02-production-readiness-qualification-foundation-core",
    "workstream": "v02-release-qualification-foundation",
    "implementation_task": SUCCESSOR_IMPLEMENTATION_TASK,
    "formal_closeout_task": SUCCESSOR_CLOSEOUT_TASK,
    "authorization_scope": expected_scope,
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
for key, expected in required_auth.items():
    if auth.get(key) != expected:
        raise SystemExit(f"authorization mismatch {key}: {auth.get(key)!r}")
active = auth.get("active_authorizations")
if active != [
    {
        "authorization_transaction_id": SUCCESSOR_AUTHORIZATION_ID,
        "implementation_task": SUCCESSOR_IMPLEMENTATION_TASK,
        "formal_closeout_task": SUCCESSOR_CLOSEOUT_TASK,
        "authorization_active": True,
        "authorization_consumed": False,
        "authorization_expired": False,
        "authorization_reusable": False,
    }
]:
    raise SystemExit("v0.2 qualification active authorization list mismatch")

approved = auth.get("approved_capabilities", {})
for key, value in approved.items():
    if value is not True:
        raise SystemExit(f"approved capability not true: {key}")
prohibited = auth.get("prohibited_capabilities", {})
for key, value in prohibited.items():
    if value is not False:
        raise SystemExit(f"prohibited capability not false: {key}")
limits = auth.get("resource_limits", {})
for key, value in limits.items():
    if key.startswith("maximum_") and key in auth.get("zero_resource_limit_keys", []):
        if value != 0:
            raise SystemExit(f"zero resource limit not zero: {key}")
for path in auth.get("implemented_source_scope", []):
    if not (root / path).exists():
        raise SystemExit(f"AION-239 implemented source is absent: {path}")
if not (root / "scripts/v02-release-qualification-local-run.py").exists():
    raise SystemExit("AION-239 local runner is absent")
pilot = root / (
    "examples/v02-release-qualification/"
    "v02-production-readiness-qualification-foundation-pilot-evidence.json"
)
if not pilot.exists():
    raise SystemExit("AION-239 pilot evidence is absent")
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

echo "v0.2 release qualification program authorization PASS"
