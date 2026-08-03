#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_BRAIN_PYTHON="$PYTHON_BIN"

./scripts/v02-release-qualification-foundation-no-go-regression.sh

PYTHONPATH="$ROOT_DIR/scripts/lib:$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

from aion_brain.contracts import v02_release_qualification as c
from aion_brain.v02_release_qualification import (
    ControlledV02ReleaseQualificationService,
)
import v02_release_qualification_foundation_operator_evaluation as aion240
import v02_staging_qualification_operator_evaluation as aion242

root = Path.cwd()
source_scope = [
    "services/brain-api/src/aion_brain/contracts/v02_release_qualification.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/__init__.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/authorization.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/gap_matrix.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/production_auth_composition.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/request_identity.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/replay_provisioning.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/identity_provider.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/key_lifecycle.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/protected_material.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/credential_lifecycle.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/token_lifecycle.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/session_lifecycle.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/deployment_manifest.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/artifact_provenance.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/rollback.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/observability.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/threat_model.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/runtime_guard.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/release_gate.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/integrity.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/evidence.py",
]
for relative in source_scope:
    if not (root / relative).is_file():
        raise SystemExit(f"missing AION-239 source: {relative}")
if not (root / "scripts/v02-release-qualification-local-run.py").is_file():
    raise SystemExit("missing uninstalled local runner")

program = json.loads(
    Path("docs/v02-release-qualification/program-ledger.json").read_text(
        encoding="utf-8"
    )
)
auth = json.loads(
    Path("docs/v02-release-qualification/authorization-ledger.json").read_text(
        encoding="utf-8"
    )
)
post_closeout_state = (
    "v02_qualification_foundation_evaluated_controlled_staging_qualification_"
    "authorized_not_implemented"
)
aion241_final_state = (
    "controlled_isolated_staging_qualification_implemented_pilot_complete_"
    "pending_closeout"
)
aion242_final_state = (
    "controlled_staging_qualification_evaluated_release_candidate_build_"
    "authorized_not_implemented"
)
aion243_final_state = (
    "deterministic_v02_release_candidate_artifact_built_local_candidate_"
    "retained_pending_final_evaluation"
)
aion244_prepublication_state = (
    "v02_release_candidate_final_evaluation_passed_pending_rc1_prerelease_"
    "publication"
)
aion243_evidence_exists = (
    root / "examples/v02-release-qualification/v02-release-candidate-artifact-build-evidence.json"
).is_file()
aion241_controlled_state = "implemented_isolated_local_pilot_complete_pending_AION-242_closeout"
for label, payload in (("program", program), ("authorization", auth)):
    if payload["program_state"] == aion244_prepublication_state:
        required = {
            "program_id": aion240.PROGRAM_ID,
            "v02_release_qualification_program_authorized": True,
            "v02_release_qualification_program_implemented": True,
            "v02_release_qualification_foundation_authorized": True,
            "v02_release_qualification_foundation_implemented": True,
            "v02_release_qualification_foundation_state": c.FOUNDATION_STATE,
            "local_qualification_pilot_completed": True,
            "disabled_local_qualification_simulator_available": True,
            "v02_release_qualification_foundation_operator_evaluation_passed": True,
            "v02_release_qualification_foundation_operator_evaluation_id": aion240.EVALUATION_ID,
            "v02_release_qualification_foundation_operator_evaluation_decision": aion240.PASS_DECISION,
            "controlled_staging_qualification_authorized": True,
            "controlled_staging_qualification_implemented": True,
            "controlled_staging_qualification_state": aion241_controlled_state,
            "controlled_staging_qualification_operator_evaluation_passed": True,
            "controlled_staging_qualification_operator_evaluation_id": aion242.EVALUATION_ID,
            "controlled_staging_qualification_operator_evaluation_decision": aion242.PASS_DECISION,
            "active_v02_release_qualification_authorization_count": 1,
            "active_v02_release_qualification_authorization": "AION-244-V02REL-0001",
            "active_v02_release_qualification_task": "AION-244",
            "formal_closeout_task": "AION-244",
            "final_planned_task": "AION-244",
            "authorization_active": True,
            "authorization_consumed": False,
            "authorization_expired": False,
            "authorization_reusable": False,
            "release_candidate_artifact_build_authorized": True,
            "release_candidate_artifact_build_implemented": True,
            "release_candidate_created": True,
            "release_candidate_creation_enabled": False,
            "release_candidate_published": False,
            "release_candidate_final_evaluation_passed": True,
            "release_candidate_prerelease": True,
            "release_candidate_promoted": False,
            "v02_release_candidate_ready": True,
            "production_runtime_authorized": False,
            "production_deployment_enabled": False,
            "v02_release_ready": False,
            "v02_tag_created": False,
            "v02_release_created": False,
            "active_staging_resources": 0,
        }
        for key, expected in required.items():
            if payload.get(key) != expected:
                raise SystemExit(f"{label} AION-244 prepublication mismatch {key}: {payload.get(key)!r}")
        closeout = payload.get("aion_242_authorization_closeout", {})
        if closeout.get("authorization_transaction_id") != aion242.NEXT_AUTHORIZATION_ID:
            raise SystemExit(f"{label} missing AION-242 closeout after AION-244")
        if closeout.get("authorization_active") is not False or closeout.get("authorization_consumed") is not True:
            raise SystemExit(f"{label} AION-242 closeout state mismatch after AION-244")
        publication_auth = payload.get("aion_244_publication_authorization", {})
        if publication_auth.get("authorization_transaction_id") != "AION-244-V02REL-0001":
            raise SystemExit(f"{label} missing AION-244 publication authorization")
        if publication_auth.get("authorization_active") is not True or publication_auth.get("authorization_consumed") is not False:
            raise SystemExit(f"{label} AION-244 publication authorization state mismatch")
        if not aion243_evidence_exists:
            raise SystemExit(f"{label} AION-243 evidence file is required for AION-244 state")
        if any(payload["prohibited_capabilities"].values()):
            raise SystemExit(f"{label} has enabled prohibited capability")
        continue
    if payload["program_state"] in {aion242_final_state, aion243_final_state}:
        aion243_complete = payload["program_state"] == aion243_final_state
        required = {
            "program_id": aion240.PROGRAM_ID,
            "v02_release_qualification_program_authorized": True,
            "v02_release_qualification_program_implemented": True,
            "v02_release_qualification_foundation_authorized": True,
            "v02_release_qualification_foundation_implemented": True,
            "v02_release_qualification_foundation_state": c.FOUNDATION_STATE,
            "local_qualification_pilot_completed": True,
            "disabled_local_qualification_simulator_available": True,
            "v02_release_qualification_foundation_operator_evaluation_passed": True,
            "v02_release_qualification_foundation_operator_evaluation_id": aion240.EVALUATION_ID,
            "v02_release_qualification_foundation_operator_evaluation_decision": aion240.PASS_DECISION,
            "controlled_staging_qualification_authorized": True,
            "controlled_staging_qualification_implemented": True,
            "controlled_staging_qualification_state": aion241_controlled_state,
            "controlled_staging_qualification_operator_evaluation_passed": True,
            "controlled_staging_qualification_operator_evaluation_id": aion242.EVALUATION_ID,
            "controlled_staging_qualification_operator_evaluation_decision": aion242.PASS_DECISION,
            "active_v02_release_qualification_authorization_count": 1,
            "active_v02_release_qualification_authorization": aion242.NEXT_AUTHORIZATION_ID,
            "active_v02_release_qualification_task": aion242.NEXT_IMPLEMENTATION_TASK,
            "formal_closeout_task": aion242.NEXT_FORMAL_CLOSEOUT_TASK,
            "final_planned_task": aion242.FINAL_PLANNED_TASK,
            "authorization_active": True,
            "authorization_consumed": False,
            "authorization_expired": False,
            "authorization_reusable": False,
            "release_candidate_artifact_build_authorized": True,
            "release_candidate_artifact_build_implemented": aion243_complete,
            "release_candidate_created": aion243_complete,
            "release_candidate_published": False,
            "release_candidate_creation_enabled": True,
            "production_runtime_authorized": False,
            "production_deployment_enabled": False,
            "v02_release_ready": False,
            "v02_tag_created": False,
            "v02_release_created": False,
            "active_staging_resources": 0,
        }
        for key, expected in required.items():
            if payload.get(key) != expected:
                raise SystemExit(f"{label} AION-242 final mismatch {key}: {payload.get(key)!r}")
        if aion243_complete:
            if not aion243_evidence_exists:
                raise SystemExit(f"{label} AION-243 evidence file is required for local candidate state")
            if payload.get("candidate_bundle_retained") is not True:
                raise SystemExit(f"{label} AION-243 candidate bundle retention missing")
            if payload.get("candidate_local_image_retained") is not True:
                raise SystemExit(f"{label} AION-243 candidate image retention missing")
        if payload.get("aion_239_resource_limits") != c.resource_limits().model_dump():
            raise SystemExit(f"{label} AION-239 resource limits mismatch")
        expected_aion241_limits = {
            **aion240.POSITIVE_AION241_LIMITS,
            **{key: 0 for key in aion240.ZERO_AION241_LIMITS},
        }
        if payload.get("aion_241_resource_limits") != expected_aion241_limits:
            raise SystemExit(f"{label} AION-241 retained resource limits mismatch")
        expected_aion243_limits = {
            **aion242.POSITIVE_AION243_LIMITS,
            **{key: 0 for key in aion242.ZERO_AION243_LIMITS},
        }
        resource_limits = payload.get("resource_limits", {})
        if isinstance(resource_limits, dict) and isinstance(resource_limits.get("limits"), dict):
            resource_limits = resource_limits["limits"]
        if resource_limits != expected_aion243_limits:
            raise SystemExit(f"{label} AION-243 resource limits mismatch")
        closed = payload.get("aion_240_authorization_closeout", {})
        if closed.get("authorization_transaction_id") != aion242.CURRENT_AUTHORIZATION_ID:
            raise SystemExit(f"{label} missing AION-240 closeout")
        if closed.get("authorization_active") is not False:
            raise SystemExit(f"{label} AION-240 closeout active flag mismatch")
        if closed.get("authorization_consumed") is not True:
            raise SystemExit(f"{label} AION-240 closeout consumed flag mismatch")
        if closed.get("authorization_expired") is not True:
            raise SystemExit(f"{label} AION-240 closeout expired flag mismatch")
        if closed.get("authorization_reusable") is not False:
            raise SystemExit(f"{label} AION-240 closeout reusable flag mismatch")
        record = payload.get("aion_241_record", {})
        if record.get("ci_result") != "pass":
            raise SystemExit(f"{label} AION-241 CI reconciliation mismatch")
        if record.get("feature_commits") != [aion242.IMPLEMENTATION_COMMIT, aion242.EVIDENCE_COMMIT]:
            raise SystemExit(f"{label} AION-241 feature commits mismatch")
        if record.get("pull_requests") != [aion242.IMPLEMENTATION_PR]:
            raise SystemExit(f"{label} AION-241 PR reconciliation mismatch")
        if record.get("merge_commits") != [aion242.IMPLEMENTATION_MERGE_COMMIT]:
            raise SystemExit(f"{label} AION-241 merge commit mismatch")
        if any(payload["prohibited_capabilities"].values()):
            raise SystemExit(f"{label} has enabled prohibited capability")
        continue
    if payload["program_state"] in {post_closeout_state, aion241_final_state}:
        aion241_complete = payload["program_state"] == aion241_final_state
        required = {
            "program_id": aion240.PROGRAM_ID,
            "v02_release_qualification_program_authorized": True,
            "v02_release_qualification_program_implemented": True,
            "v02_release_qualification_foundation_authorized": True,
            "v02_release_qualification_foundation_implemented": True,
            "v02_release_qualification_foundation_state": c.FOUNDATION_STATE,
            "local_qualification_pilot_completed": True,
            "disabled_local_qualification_simulator_available": True,
            "v02_release_qualification_foundation_operator_evaluation_passed": True,
            "v02_release_qualification_foundation_operator_evaluation_id": aion240.EVALUATION_ID,
            "v02_release_qualification_foundation_operator_evaluation_decision": aion240.PASS_DECISION,
            "active_v02_release_qualification_authorization_count": 1,
            "active_v02_release_qualification_authorization": aion240.NEXT_AUTHORIZATION_ID,
            "active_v02_release_qualification_task": aion240.NEXT_IMPLEMENTATION_TASK,
            "formal_closeout_task": aion240.NEXT_FORMAL_CLOSEOUT_TASK,
            "final_planned_task": aion240.FINAL_PLANNED_TASK,
            "authorization_active": True,
            "authorization_consumed": False,
            "authorization_expired": False,
            "authorization_reusable": False,
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
        if payload.get("aion_239_resource_limits") != c.resource_limits().model_dump():
            raise SystemExit(f"{label} AION-239 resource limits mismatch")
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
        record = payload.get("aion_239_record", {})
        if record.get("authorization_state") != "consumed_by_AION-239_closed_by_AION-240":
            raise SystemExit(f"{label} AION-239 authorization state mismatch")
        if record.get("ci_result") != "pass":
            raise SystemExit(f"{label} AION-239 CI reconciliation mismatch")
        if record.get("feature_commits") != [aion240.IMPLEMENTATION_COMMIT, aion240.CI_FIX_COMMIT]:
            raise SystemExit(f"{label} AION-239 feature commits mismatch")
        if record.get("merge_commits") != [aion240.IMPLEMENTATION_MERGE_COMMIT]:
            raise SystemExit(f"{label} AION-239 merge commit mismatch")
        if any(payload["prohibited_capabilities"].values()):
            raise SystemExit(f"{label} has enabled prohibited capability")
        resource_limits = payload.get("resource_limits", {})
        if isinstance(resource_limits, dict) and isinstance(resource_limits.get("limits"), dict):
            resource_limits = resource_limits["limits"]
        aion_241_resource_limits = payload.get("aion_241_resource_limits", {})
        if (
            isinstance(aion_241_resource_limits, dict)
            and isinstance(aion_241_resource_limits.get("limits"), dict)
        ):
            aion_241_resource_limits = aion_241_resource_limits["limits"]
        if resource_limits != aion_241_resource_limits:
            raise SystemExit(f"{label} AION-241 resource limits mismatch")
        for key, expected in aion240.POSITIVE_AION241_LIMITS.items():
            if resource_limits.get(key) != expected:
                raise SystemExit(f"{label} AION-241 positive resource limit mismatch: {key}")
        for key in aion240.ZERO_AION241_LIMITS:
            if resource_limits.get(key) != 0:
                raise SystemExit(f"{label} AION-241 zero resource limit mismatch: {key}")
        continue
    if payload["program_state"] != c.FOUNDATION_PROGRAM_STATE:
        raise SystemExit(f"{label} program_state mismatch")
    if payload["v02_release_qualification_program_authorized"] is not True:
        raise SystemExit(f"{label} program not authorized")
    if payload["v02_release_qualification_program_implemented"] is not True:
        raise SystemExit(f"{label} program not implemented")
    if payload["v02_release_qualification_foundation_implemented"] is not True:
        raise SystemExit(f"{label} foundation not implemented")
    if payload["v02_release_qualification_foundation_state"] != c.FOUNDATION_STATE:
        raise SystemExit(f"{label} foundation state mismatch")
    if payload["active_v02_release_qualification_authorization"] != c.AUTHORIZATION_TRANSACTION_ID:
        raise SystemExit(f"{label} active authorization mismatch")
    if payload["active_v02_release_qualification_task"] != c.IMPLEMENTATION_TASK:
        raise SystemExit(f"{label} active task mismatch")
    if payload["formal_closeout_task"] != c.FORMAL_CLOSEOUT_TASK:
        raise SystemExit(f"{label} closeout task mismatch")
    if payload["aion_238_delivery_reconciliation"]["merge_commits"] != [c.AION_238_MERGE_COMMIT]:
        raise SystemExit(f"{label} AION-238 merge reconciliation mismatch")
    if payload["resource_limits"] != c.resource_limits().model_dump():
        raise SystemExit(f"{label} resource limits mismatch")
    if payload["v02_release_ready"] is not False:
        raise SystemExit(f"{label} must keep v02_release_ready=false")
    if any(payload["prohibited_capabilities"].values()):
        raise SystemExit(f"{label} has enabled prohibited capability")

service = ControlledV02ReleaseQualificationService()
result = service.run_canonical_disabled_pilot()
if result.readiness_domains_evaluated != len(c.READINESS_DOMAINS):
    raise SystemExit("service did not evaluate all readiness domains")
if result.release_gates_evaluated != len(c.CANONICAL_RELEASE_GATE_IDS):
    raise SystemExit("service did not evaluate all release gates")
if result.v02_release_ready is not False or result.v02_release_candidate_created is not False:
    raise SystemExit("service must preserve release hold")
if sum(result.prohibited_effect_counters.values()) != 0:
    raise SystemExit("service produced prohibited effects")
PY

PYTHONPATH="$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" -m pytest \
  services/brain-api/tests/test_v02_release_qualification_contracts_aion239.py \
  services/brain-api/tests/test_v02_release_qualification_service_aion239.py \
  services/brain-api/tests/test_v02_release_qualification_pilot_evidence_aion239.py \
  services/brain-api/tests/test_v02_release_qualification_no_go_aion239.py \
  services/brain-api/tests/test_v02_release_qualification_runner_aion239.py \
  services/brain-api/tests/test_secure_runtime_integration_final_closeout_aion238.py \
  -q

./scripts/v02-release-qualification-program-authorization-check.sh >/dev/null
./scripts/v02-release-qualification-foundation-pilot-evidence-check.sh >/dev/null

echo "v0.2 release qualification foundation PASS"
