from __future__ import annotations

import json
from pathlib import Path

from aion_brain.contracts import v02_release_qualification as c

REPO_ROOT = Path(__file__).resolve().parents[3]
PILOT = REPO_ROOT / (
    "examples/v02-release-qualification/"
    "v02-production-readiness-qualification-foundation-pilot-evidence.json"
)


def load_json(relative: str) -> dict:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


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


def test_ledgers_record_implemented_foundation_and_keep_authorization_active():
    program = load_json("docs/v02-release-qualification/program-ledger.json")
    auth = load_json("docs/v02-release-qualification/authorization-ledger.json")

    for payload in (program, auth):
        assert payload["program_state"] == c.FOUNDATION_PROGRAM_STATE
        assert payload["v02_release_qualification_program_authorized"] is True
        assert payload["v02_release_qualification_program_implemented"] is True
        assert payload["v02_release_qualification_foundation_authorized"] is True
        assert payload["v02_release_qualification_foundation_implemented"] is True
        assert payload["v02_release_qualification_foundation_state"] == c.FOUNDATION_STATE
        assert payload["local_qualification_pilot_completed"] is True
        assert payload["disabled_local_qualification_simulator_available"] is True
        assert payload["active_v02_release_qualification_authorization"] == (
            c.AUTHORIZATION_TRANSACTION_ID
        )
        assert payload["active_v02_release_qualification_task"] == c.IMPLEMENTATION_TASK
        assert payload["formal_closeout_task"] == c.FORMAL_CLOSEOUT_TASK
        assert payload["final_planned_task"] == c.FINAL_PLANNED_TASK
        assert payload["authorization_active"] is True
        assert payload["authorization_consumed"] is False
        assert payload["authorization_expired"] is False
        assert payload["authorization_reusable"] is False
        assert payload["v02_release_ready"] is False
        assert payload["v02_tag_created"] is False
        assert payload["v02_release_created"] is False
        assert not any(payload["prohibited_capabilities"].values())
        for key in payload["zero_resource_limit_keys"]:
            assert payload["resource_limits"][key] == 0


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
