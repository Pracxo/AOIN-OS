from __future__ import annotations

import json
from pathlib import Path

from secure_runtime_integration_final_evaluation_test_support import (
    evaluation_module,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
AION240_AUTHORIZATION_ID = "AION-240-V02RQ-0002"
AION242_AUTHORIZATION_ID = "AION-242-V02RQ-0003"
AION240_PASS_DECISION = (
    "DISABLED_V02_PRODUCTION_READINESS_QUALIFICATION_FOUNDATION_OPERATOR_"
    "EVALUATION_PASS_RECOMMEND_CONTROLLED_ISOLATED_STAGING_ARTIFACT_AND_"
    "ROLLBACK_DRILL_QUALIFICATION_AUTHORIZATION"
)
AION242_PASS_DECISION = (
    "CONTROLLED_ISOLATED_LOCAL_STAGING_QUALIFICATION_OPERATOR_EVALUATION_PASS_"
    "RECOMMEND_DETERMINISTIC_V02_RELEASE_CANDIDATE_ARTIFACT_BUILD_AUTHORIZATION"
)
AION244_AUTHORIZATION_ID = "AION-244-V02REL-0001"
AION244_PASS_DECISION = (
    "DETERMINISTIC_LOCAL_V02_RELEASE_CANDIDATE_FINAL_EVALUATION_PASS_AUTHORIZE_"
    "AION_V0_2_0_RC_1_ANNOTATED_TAG_AND_GITHUB_PRERELEASE_PUBLICATION"
)
AION240_FAIL_DECISION = (
    "DISABLED_V02_PRODUCTION_READINESS_QUALIFICATION_FOUNDATION_OPERATOR_"
    "EVALUATION_FAIL_REMAIN_DESIGN_AND_LOCAL_SIMULATION_ONLY"
)


def load_json(relative: str) -> dict:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def resource_limit_map(payload: dict) -> dict:
    limits = payload["resource_limits"]
    if isinstance(limits.get("limits"), dict):
        return limits["limits"]
    return limits


def test_aion238_report_closes_sri_program_and_authorization():
    module = evaluation_module()
    report = load_json(
        "examples/secure-runtime-integration/"
        "secure-runtime-integration-final-evaluation-report.json"
    )
    program = load_json("docs/secure-runtime-integration/program-ledger.json")
    auth = load_json("docs/secure-runtime-integration/authorization-ledger.json")

    module.validate_report(report)
    assert report["decision"] == module.PASS_DECISION
    assert report["scenario_count"] == 28
    assert set(report["scenario_results"].values()) == {"pass"}
    assert all(report["hard_gate_results"].values())

    assert program["program_state"] == "secure_runtime_integration_program_complete"
    assert program["secure_runtime_integration_program_complete"] is True
    assert program["secure_runtime_integration_final_evaluation_id"] == "AION-SRIPE-004"
    assert program["secure_runtime_integration_final_evaluation_decision"] == (
        module.PASS_DECISION
    )
    assert program["final_completed_task"] == "AION-238"
    assert program["active_sri_implementation_authorization_count"] == 0
    assert program["active_sri_implementation_authorization"] is None
    assert program["active_sri_implementation_task"] is None
    assert program["formal_closeout_task"] is None
    assert program["next_sri_implementation_task"] is None

    assert auth["authorization_transaction_id"] == "AION-236-SRI-0004"
    assert auth["authorization_active"] is False
    assert auth["authorization_consumed"] is True
    assert auth["authorization_consumed_by_task"] == "AION-237"
    assert auth["authorization_consumed_by_prs"] == [156]
    assert auth["authorization_consumed_by_feature_commits"] == [
        "df1f89e1708638e32aef0532fb37ed150b85b600"
    ]
    assert auth["authorization_consumed_by_merge_commits"] == [
        "55f2721bb036886a693a36d870d49f49f7ecc6d1"
    ]
    assert auth["authorization_expired"] is True
    assert auth["authorization_reusable"] is False
    assert auth["authorization_closed_by_task"] == "AION-238"
    assert auth["final_sri_evaluation_id"] == "AION-SRIPE-004"
    assert auth["final_sri_evaluation_decision"] == module.PASS_DECISION
    assert auth["active_authorizations"] == []
    assert not any(item["authorization_active"] for item in auth["records"])


def test_aion237_delivery_is_reconciled_to_merged_pr_156():
    program = load_json("docs/secure-runtime-integration/program-ledger.json")
    record = program["aion_237_record"]

    assert record["ci_result"] == "pass"
    assert record["pull_requests"] == [156]
    assert record["feature_commits"] == [
        "df1f89e1708638e32aef0532fb37ed150b85b600"
    ]
    assert record["merge_commits"] == [
        "55f2721bb036886a693a36d870d49f49f7ecc6d1"
    ]
    assert record["completion_timestamp"] == "2026-08-01T11:32:50Z"
    assert record["authorization_state"] == "consumed_by_AION-237_closed_by_AION-238"
    assert record["final_evaluation_id"] == "AION-SRIPE-004"


def test_v02_release_qualification_successor_authorization_is_exact_and_disabled():
    module = evaluation_module()
    program = load_json("docs/v02-release-qualification/program-ledger.json")
    auth = load_json("docs/v02-release-qualification/authorization-ledger.json")
    final_rc1_published = (
        auth["authorization_transaction_id"] == AION244_AUTHORIZATION_ID
        and program["release_candidate_published"] is True
    )

    assert program["program_id"] == "AION-V02-RELEASE-QUALIFICATION-001"
    assert program["v02_release_qualification_program_implemented"] is True
    assert program["v02_release_qualification_foundation_implemented"] is True
    assert program["v02_release_qualification_foundation_state"] == (
        "implemented_disabled_design_and_local_simulation_pending_AION-240_closeout"
    )
    if auth["authorization_transaction_id"] == AION242_AUTHORIZATION_ID:
        assert program["parent_evaluation_id"] == "AION-V02RQPE-002"
        assert program["parent_evaluation_decision"] == AION242_PASS_DECISION
    elif auth["authorization_transaction_id"] == AION244_AUTHORIZATION_ID:
        assert program["parent_evaluation_id"] == "AION-V02RQPE-003"
        assert program["parent_evaluation_decision"] == AION244_PASS_DECISION
        assert program["release_candidate_final_evaluation_passed"] is True
        assert program["release_candidate_published"] is final_rc1_published
    else:
        assert program["parent_evaluation_id"] == "AION-SRIPE-004"
        assert program["parent_evaluation_decision"] == module.PASS_DECISION
    if final_rc1_published:
        assert program["final_planned_task"] is None
        assert auth["authorization_active"] is False
        assert auth["authorization_consumed"] is True
        assert auth["authorization_expired"] is True
    else:
        assert program["final_planned_task"] == "AION-244"
        assert auth["authorization_active"] is True
        assert auth["authorization_consumed"] is False
        assert auth["authorization_expired"] is False
    assert auth["authorization_reusable"] is False

    if auth["authorization_transaction_id"] == AION240_AUTHORIZATION_ID:
        post_closeout_state = (
            "v02_qualification_foundation_evaluated_controlled_staging_qualification_"
            "authorized_not_implemented"
        )
        aion241_implemented_state = (
            "controlled_isolated_staging_qualification_implemented_pilot_complete_pending_"
            "closeout"
        )
        expected_program_state = (
            aion241_implemented_state
            if program.get("controlled_staging_qualification_implemented") is True
            else post_closeout_state
        )
        assert program["program_state"] == expected_program_state
        assert program["active_v02_release_qualification_authorization_count"] == 1
        assert program["active_v02_release_qualification_authorization"] == (
            AION240_AUTHORIZATION_ID
        )
        assert program["active_v02_release_qualification_task"] == "AION-241"
        assert program["formal_closeout_task"] == "AION-242"
        closeout = auth["aion_238_authorization_closeout"]
        assert closeout["authorization_transaction_id"] == "AION-238-V02RQ-0001"
        assert closeout["authorization_active"] is False
        assert closeout["authorization_consumed"] is True
        assert closeout["authorization_expired"] is True
        assert closeout["authorization_reusable"] is False
        assert closeout["authorization_consumed_by_task"] == "AION-239"
        assert closeout["authorization_closed_by_task"] == "AION-240"
        assert closeout["foundation_evaluation_id"] == "AION-V02RQPE-001"
        assert closeout["foundation_evaluation_decision"] == AION240_PASS_DECISION
        assert auth["approval_record_id"] == AION240_AUTHORIZATION_ID
        assert auth["parent_authorization_transaction_id"] == "AION-238-V02RQ-0001"
        assert auth["parent_evaluation_id"] == "AION-V02RQPE-001"
        assert auth["parent_evaluation_decision"] == AION240_PASS_DECISION
        assert auth["implementation_task"] == "AION-241"
        assert auth["formal_closeout_task"] == "AION-242"
        assert auth["active_authorizations"] == [
            {
                "authorization_transaction_id": AION240_AUTHORIZATION_ID,
                "implementation_task": "AION-241",
                "formal_closeout_task": "AION-242",
                "authorization_active": True,
                "authorization_consumed": False,
                "authorization_expired": False,
                "authorization_reusable": False,
            }
        ]
    elif auth["authorization_transaction_id"] == AION242_AUTHORIZATION_ID:
        aion243_evidence_exists = (
            REPO_ROOT
            / "examples/v02-release-qualification/"
            "v02-release-candidate-artifact-build-evidence.json"
        ).is_file()
        expected_program_state = (
            "deterministic_v02_release_candidate_artifact_built_local_candidate_"
            "retained_pending_final_evaluation"
            if aion243_evidence_exists
            else (
                "controlled_staging_qualification_evaluated_release_candidate_build_"
                "authorized_not_implemented"
            )
        )
        assert program["program_state"] == expected_program_state
        assert program["active_v02_release_qualification_authorization_count"] == 1
        assert program["active_v02_release_qualification_authorization"] == (
            AION242_AUTHORIZATION_ID
        )
        assert program["active_v02_release_qualification_task"] == "AION-243"
        assert program["formal_closeout_task"] == "AION-244"
        assert program["controlled_staging_qualification_implemented"] is True
        assert (
            program["controlled_staging_qualification_operator_evaluation_passed"]
            is True
        )
        assert program["release_candidate_artifact_build_authorized"] is True
        assert program["release_candidate_artifact_build_implemented"] is (
            aion243_evidence_exists
        )
        assert program["release_candidate_created"] is aion243_evidence_exists
        if aion243_evidence_exists:
            assert program["candidate_bundle_retained"] is True
            assert program["candidate_local_image_retained"] is True
        assert program["release_candidate_published"] is False
        assert program["production_runtime_authorized"] is False
        assert program["production_deployment_enabled"] is False
        closeout = auth["aion_240_authorization_closeout"]
        assert closeout["authorization_transaction_id"] == AION240_AUTHORIZATION_ID
        assert closeout["authorization_active"] is False
        assert closeout["authorization_consumed"] is True
        assert closeout["authorization_expired"] is True
        assert closeout["authorization_reusable"] is False
        assert closeout["authorization_consumed_by_task"] == "AION-241"
        assert closeout["authorization_closed_by_task"] == "AION-242"
        assert closeout["staging_evaluation_id"] == "AION-V02RQPE-002"
        assert closeout["staging_evaluation_decision"] == AION242_PASS_DECISION
        assert auth["approval_record_id"] == AION242_AUTHORIZATION_ID
        assert auth["parent_authorization_transaction_id"] == AION240_AUTHORIZATION_ID
        assert auth["parent_evaluation_id"] == "AION-V02RQPE-002"
        assert auth["parent_evaluation_decision"] == AION242_PASS_DECISION
        assert auth["implementation_task"] == "AION-243"
        assert auth["formal_closeout_task"] == "AION-244"
        assert auth["active_authorizations"] == [
            {
                "authorization_transaction_id": AION242_AUTHORIZATION_ID,
                "implementation_task": "AION-243",
                "formal_closeout_task": "AION-244",
                "authorization_active": True,
                "authorization_consumed": False,
                "authorization_expired": False,
                "authorization_reusable": False,
            }
        ]
    elif auth["authorization_transaction_id"] == AION244_AUTHORIZATION_ID:
        assert program["program_state"] == (
            "v02_release_qualification_program_complete_rc1_prerelease_published"
        )
        assert program["active_v02_release_qualification_authorization_count"] == 0
        assert program["active_v02_release_qualification_authorization"] is None
        assert program["active_v02_release_qualification_task"] is None
        assert program["formal_closeout_task"] is None
        assert program["release_candidate_final_evaluation_passed"] is True
        assert program["release_candidate_published"] is True
        assert program["release_candidate_promoted"] is False
        assert program["v02_tag_created"] is True
        assert program["v02_tag_name"] == "aion-v0.2.0-rc.1"
        assert program["v02_release_created"] is True
        assert program["v02_stable_tag_created"] is False
        assert program["v02_stable_release_created"] is False
        assert auth["approval_record_id"] == AION244_AUTHORIZATION_ID
        assert auth["parent_authorization_transaction_id"] == AION242_AUTHORIZATION_ID
        assert auth["parent_evaluation_id"] == "AION-V02RQPE-003"
        assert auth["parent_evaluation_decision"] == AION244_PASS_DECISION
        assert auth["authorization_active"] is False
        assert auth["authorization_consumed"] is True
        assert auth["authorization_expired"] is True
        assert auth["authorization_reusable"] is False
        publication = auth["aion_244_publication_authorization"]
        assert publication["authorization_transaction_id"] == AION244_AUTHORIZATION_ID
        assert publication["authorization_active"] is False
        assert publication["authorization_consumed"] is True
    else:
        assert program["program_state"] == (
            "v02_release_qualification_foundation_implemented_disabled_pending_closeout"
        )
        assert program["active_v02_release_qualification_authorization_count"] == 1
        assert program["active_v02_release_qualification_authorization"] == (
            "AION-238-V02RQ-0001"
        )
        assert program["active_v02_release_qualification_task"] == "AION-239"
        assert program["formal_closeout_task"] == "AION-240"
        assert auth["authorization_transaction_id"] == "AION-238-V02RQ-0001"
        assert auth["approval_record_id"] == "AION-238-V02RQ-0001"
        assert auth["implementation_task"] == "AION-239"
        assert auth["formal_closeout_task"] == "AION-240"
        assert auth["active_authorizations"] == [
            {
                "authorization_transaction_id": "AION-238-V02RQ-0001",
                "implementation_task": "AION-239",
                "formal_closeout_task": "AION-240",
                "authorization_active": True,
                "authorization_consumed": False,
                "authorization_expired": False,
                "authorization_reusable": False,
            }
        ]
    assert all(auth["approved_capabilities"].values())
    assert not any(auth["prohibited_capabilities"].values())

    limits = resource_limit_map(auth)
    for key in auth["zero_resource_limit_keys"]:
        assert limits[key] == 0
    for path in auth["implemented_source_scope"]:
        assert (REPO_ROOT / path).exists()
    assert (REPO_ROOT / "scripts/v02-release-qualification-local-run.py").exists()
    assert auth["local_qualification_pilot_completed"] is True
    assert auth["v02_release_ready"] is (
        auth["authorization_transaction_id"] == AION244_AUTHORIZATION_ID
        and auth.get("release_candidate_published") is True
    )


def test_release_state_remains_false_and_fail_does_not_authorize_successor():
    module = evaluation_module()
    sri_program = load_json("docs/secure-runtime-integration/program-ledger.json")
    v02_program = load_json("docs/v02-release-qualification/program-ledger.json")
    v02_auth = load_json("docs/v02-release-qualification/authorization-ledger.json")

    assert sri_program["v02_release_ready"] is False
    assert sri_program["v02_tag_created"] is False
    assert sri_program["v02_release_created"] is False
    final_rc1_published = (
        v02_auth["authorization_transaction_id"] == AION244_AUTHORIZATION_ID
        and v02_auth.get("release_candidate_published") is True
    )
    assert v02_program["v02_release_ready"] is final_rc1_published
    assert v02_program["v02_tag_created"] is final_rc1_published
    assert v02_program["v02_release_created"] is final_rc1_published
    if v02_auth["authorization_transaction_id"] == AION240_AUTHORIZATION_ID:
        assert v02_auth["parent_evaluation_decision"] == AION240_PASS_DECISION
    elif v02_auth["authorization_transaction_id"] == AION242_AUTHORIZATION_ID:
        assert v02_auth["parent_evaluation_decision"] == AION242_PASS_DECISION
    elif v02_auth["authorization_transaction_id"] == AION244_AUTHORIZATION_ID:
        assert v02_auth["parent_evaluation_decision"] == AION244_PASS_DECISION
        assert v02_auth["release_candidate_published"] is True
        assert v02_auth["release_candidate_promoted"] is False
        assert v02_auth["v02_stable_tag_created"] is False
        assert v02_auth["v02_stable_release_created"] is False
    else:
        assert v02_auth["parent_evaluation_decision"] == module.PASS_DECISION
    serialized = json.dumps((v02_program, v02_auth), sort_keys=True)
    assert module.FAIL_DECISION not in serialized
    assert AION240_FAIL_DECISION not in serialized
