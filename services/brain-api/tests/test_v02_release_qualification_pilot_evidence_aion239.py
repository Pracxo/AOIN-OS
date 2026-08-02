from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from aion_brain.contracts import v02_release_qualification as c

REPO_ROOT = Path(__file__).resolve().parents[3]
PILOT = REPO_ROOT / (
    "examples/v02-release-qualification/"
    "v02-production-readiness-qualification-foundation-pilot-evidence.json"
)
HARNESS_PATH = (
    REPO_ROOT / "scripts/lib/v02_release_qualification_foundation_operator_evaluation.py"
)
AION242_HARNESS_PATH = (
    REPO_ROOT / "scripts/lib/v02_staging_qualification_operator_evaluation.py"
)


def load_harness():
    spec = importlib.util.spec_from_file_location("aion240_eval", HARNESS_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_aion242_harness():
    spec = importlib.util.spec_from_file_location("aion242_eval", AION242_HARNESS_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_json(relative: str) -> dict:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def resource_limit_map(payload: dict) -> dict:
    limits = payload["resource_limits"]
    if isinstance(limits.get("limits"), dict):
        return limits["limits"]
    return limits


def test_committed_pilot_evidence_fingerprint_and_counters_are_exact():
    evidence = json.loads(PILOT.read_text(encoding="utf-8"))
    expected = c.v02_qualification_fingerprint(
        {key: value for key, value in evidence.items() if key != "report_fingerprint"}
    )

    assert evidence["report_fingerprint"] == expected
    assert evidence["pilot_id"] == c.PILOT_ID
    assert evidence["authorization_id"] == c.AUTHORIZATION_TRANSACTION_ID
    assert evidence["program_id"] == c.PROGRAM_ID
    assert evidence["mode"] == "deterministic-local-simulation"
    assert evidence["qualification_decision"] == c.FOUNDATION_DECISION
    assert evidence["readiness_domains_evaluated"] == 20
    assert evidence["readiness_gaps_evaluated"] == 20
    assert evidence["release_gates_evaluated"] == 24
    assert evidence["staging_evidence_required"] is True
    assert evidence["production_evidence_required"] is True
    assert evidence["v02_release_ready"] is False
    assert evidence["v02_release_candidate_created"] is False
    assert evidence["integrity_passed"] is True
    assert evidence["temporary_files_retained"] == 0
    assert evidence["temporary_paths_retained"] == 0
    assert evidence["redacted"] is True
    assert evidence["production_effect"] is False
    assert evidence["runtime_effect"] is False
    assert evidence["prohibited_effect_counters"] == c.PROHIBITED_EFFECT_COUNTERS
    for key, expected_value in c.PROHIBITED_EFFECT_COUNTERS.items():
        assert evidence[key] == expected_value


def test_ledgers_record_implemented_foundation_and_current_authorization_state():
    harness = load_harness()
    aion242 = load_aion242_harness()
    program = load_json("docs/v02-release-qualification/program-ledger.json")
    auth = load_json("docs/v02-release-qualification/authorization-ledger.json")
    post_closeout_state = (
        "v02_qualification_foundation_evaluated_controlled_staging_qualification_"
        "authorized_not_implemented"
    )
    aion241_implemented_state = (
        "controlled_isolated_staging_qualification_implemented_pilot_complete_pending_"
        "closeout"
    )
    aion242_authorized_state = (
        "controlled_staging_qualification_evaluated_release_candidate_build_"
        "authorized_not_implemented"
    )
    aion243_local_candidate_state = (
        "deterministic_v02_release_candidate_artifact_built_local_candidate_"
        "retained_pending_final_evaluation"
    )
    aion243_evidence_exists = (
        REPO_ROOT
        / "examples/v02-release-qualification/"
        "v02-release-candidate-artifact-build-evidence.json"
    ).is_file()

    for payload in (program, auth):
        assert payload["v02_release_qualification_program_authorized"] is True
        assert payload["v02_release_qualification_program_implemented"] is True
        assert payload["v02_release_qualification_foundation_authorized"] is True
        assert payload["v02_release_qualification_foundation_implemented"] is True
        assert payload["v02_release_qualification_foundation_state"] == c.FOUNDATION_STATE
        assert payload["local_qualification_pilot_completed"] is True
        assert payload["disabled_local_qualification_simulator_available"] is True
        assert payload["v02_release_ready"] is False
        assert payload["v02_tag_created"] is False
        assert payload["v02_release_created"] is False
        assert not any(payload["prohibited_capabilities"].values())

        if payload["active_v02_release_qualification_authorization"] == (
            aion242.NEXT_AUTHORIZATION_ID
        ):
            expected_program_state = (
                aion243_local_candidate_state
                if aion243_evidence_exists
                else aion242_authorized_state
            )
            assert payload["program_state"] == expected_program_state
            assert (
                payload["v02_release_qualification_foundation_operator_evaluation_passed"]
                is True
            )
            assert (
                payload["v02_release_qualification_foundation_operator_evaluation_id"]
                == harness.EVALUATION_ID
            )
            assert (
                payload["v02_release_qualification_foundation_operator_evaluation_decision"]
                == harness.PASS_DECISION
            )
            assert payload["controlled_staging_qualification_authorized"] is True
            assert payload["controlled_staging_qualification_implemented"] is True
            assert (
                payload["controlled_staging_qualification_operator_evaluation_passed"]
                is True
            )
            assert (
                payload["controlled_staging_qualification_operator_evaluation_id"]
                == aion242.EVALUATION_ID
            )
            assert (
                payload["controlled_staging_qualification_operator_evaluation_decision"]
                == aion242.PASS_DECISION
            )
            assert payload["active_v02_release_qualification_authorization_count"] == 1
            assert payload["active_v02_release_qualification_task"] == (
                aion242.NEXT_IMPLEMENTATION_TASK
            )
            assert payload["formal_closeout_task"] == aion242.NEXT_FORMAL_CLOSEOUT_TASK
            assert payload["release_candidate_artifact_build_authorized"] is True
            assert payload["release_candidate_artifact_build_implemented"] is (
                aion243_evidence_exists
            )
            assert payload["release_candidate_created"] is aion243_evidence_exists
            assert payload["release_candidate_published"] is False
            if aion243_evidence_exists:
                assert payload["candidate_bundle_retained"] is True
                assert payload["candidate_local_image_retained"] is True
            assert payload["production_runtime_authorized"] is False
            assert payload["production_deployment_enabled"] is False
            closeout = payload["aion_240_authorization_closeout"]
            assert closeout["authorization_transaction_id"] == aion242.CURRENT_AUTHORIZATION_ID
            assert closeout["authorization_active"] is False
            assert closeout["authorization_consumed"] is True
            assert closeout["authorization_expired"] is True
            assert closeout["authorization_reusable"] is False
            assert payload["aion_239_resource_limits"] == c.resource_limits().model_dump()
            expected_aion243_limits = {
                **aion242.POSITIVE_AION243_LIMITS,
                **dict.fromkeys(aion242.ZERO_AION243_LIMITS, 0),
            }
            assert resource_limit_map(payload) == expected_aion243_limits
        elif payload["active_v02_release_qualification_authorization"] == (
            harness.NEXT_AUTHORIZATION_ID
        ):
            expected_program_state = (
                aion241_implemented_state
                if payload.get("controlled_staging_qualification_implemented") is True
                else post_closeout_state
            )
            assert payload["program_state"] == expected_program_state
            assert (
                payload["v02_release_qualification_foundation_operator_evaluation_passed"]
                is True
            )
            assert (
                payload["v02_release_qualification_foundation_operator_evaluation_id"]
                == harness.EVALUATION_ID
            )
            assert (
                payload["v02_release_qualification_foundation_operator_evaluation_decision"]
                == harness.PASS_DECISION
            )
            assert payload["active_v02_release_qualification_authorization_count"] == 1
            assert payload["active_v02_release_qualification_task"] == (
                harness.NEXT_IMPLEMENTATION_TASK
            )
            assert payload["formal_closeout_task"] == harness.NEXT_FORMAL_CLOSEOUT_TASK
            assert payload["controlled_staging_qualification_authorized"] is True
            assert payload["controlled_staging_qualification_implemented"] is (
                payload["program_state"] == aion241_implemented_state
            )
            closeout = payload["aion_238_authorization_closeout"]
            assert closeout["authorization_transaction_id"] == harness.CURRENT_AUTHORIZATION_ID
            assert closeout["authorization_active"] is False
            assert closeout["authorization_consumed"] is True
            assert closeout["authorization_expired"] is True
            assert closeout["authorization_reusable"] is False
            assert (
                payload["aion_239_record"]["authorization_state"]
                == "consumed_by_AION-239_closed_by_AION-240"
            )
            assert payload["aion_239_record"]["ci_result"] == "pass"
            assert payload["aion_239_resource_limits"] == c.resource_limits().model_dump()
        else:
            assert payload["program_state"] == c.FOUNDATION_PROGRAM_STATE
            assert payload["active_v02_release_qualification_authorization"] == (
                c.AUTHORIZATION_TRANSACTION_ID
            )
            assert payload["active_v02_release_qualification_task"] == c.IMPLEMENTATION_TASK
            assert payload["formal_closeout_task"] == c.FORMAL_CLOSEOUT_TASK
            limits = resource_limit_map(payload)
            for key in payload["zero_resource_limit_keys"]:
                assert limits[key] == 0
        assert payload["final_planned_task"] == c.FINAL_PLANNED_TASK
        assert payload["authorization_active"] is True
        assert payload["authorization_consumed"] is False
        assert payload["authorization_expired"] is False
        assert payload["authorization_reusable"] is False


def test_release_candidate_and_runtime_evidence_remain_holds():
    runtime_hold = load_json("examples/v02-release-qualification/runtime-hold.json")
    matrix = load_json("examples/v02-release-qualification/release-gate-matrix.json")
    candidate = load_json(
        "examples/v02-release-qualification/release-candidate-evidence-matrix.json"
    )

    assert runtime_hold["local_qualification_pilot_completed"] is True
    assert runtime_hold["production_auth_runtime_enabled"] is False
    assert runtime_hold["external_identity_provider_call_enabled"] is False
    assert runtime_hold["staging_deployment_enabled"] is False
    assert runtime_hold["v02_release_ready"] is False
    assert matrix["v02_release_ready"] is False
    assert matrix["v02_release_candidate_created"] is False
    assert len(matrix["gates"]) == 24
    assert candidate["release_candidate_authorized"] is False
    assert candidate["release_candidate_created"] is False
    assert candidate["staging_evidence_required"] is True
