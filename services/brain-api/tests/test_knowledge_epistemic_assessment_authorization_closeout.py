from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _authorization_ledger() -> dict:
    return json.loads(
        (REPO_ROOT / "docs/knowledge-intelligence/authorization-ledger.json").read_text()
    )


def _program_ledger() -> dict:
    return json.loads(
        (REPO_ROOT / "docs/knowledge-intelligence/program-ledger.json").read_text()
    )


def _authorization_records() -> list[dict]:
    return _authorization_ledger()["records"]


def test_aion_210_authorization_is_closed_consumed_and_non_reusable():
    records = _authorization_records()
    matches = [
        record
        for record in records
        if record.get("authorization_transaction_id") == "AION-210-KI-0004"
    ]
    assert len(matches) == 1
    record = matches[0]

    assert record["authorization_active"] is False
    assert record["authorization_consumed"] is True
    assert record["authorization_expired"] is True
    assert record["authorization_reusable"] is False
    assert record["authorization_consumed_by_task"] == "AION-211"
    assert record["authorization_consumed_by_prs"] == [123]
    assert record["authorization_consumed_by_feature_commits"] == [
        "9a5bfca384a1720495cce677a817acef556f9e91"
    ]
    assert record["authorization_consumed_by_merge_commits"] == [
        "737f166966aeacc2362fd62b852292264b3e2d97"
    ]
    assert record["authorization_closed_by_task"] == "AION-212"
    assert record["epistemic_assessment_operator_evaluation_id"] == "AION-EAE-001"
    assert record["evaluation_used_as_approval"] is False
    assert record["evaluation_reusable"] is False


def test_aion_210_cannot_be_the_active_authorization_after_closeout():
    active = [
        record
        for record in _authorization_records()
        if record.get("authorization_active") is True
    ]
    assert len(active) == 1
    assert active[0]["authorization_transaction_id"] == "AION-212-KI-0005"
    assert active[0]["implementation_task"] == "AION-213"


def test_aion_212_current_projection_matches_active_authorization():
    auth = _authorization_ledger()
    program = _program_ledger()
    active = [
        record
        for record in auth["records"]
        if record.get("authorization_active") is True
    ]
    assert len(active) == 1
    record = active[0]

    assert record["authorization_transaction_id"] == "AION-212-KI-0005"
    assert record["approval_record_id"] == "AION-212-KI-0005"
    assert record["candidate_id"] == "domain-expert-mesh-core"
    assert record["workstream"] == "knowledge-intelligence-domain-expert-mesh"
    assert record["implementation_task"] == "AION-213"
    assert record["formal_closeout_task"] == "AION-214"
    assert record["authorization_active"] is True
    assert record["authorization_consumed"] is False
    assert record["authorization_expired"] is False
    assert record["authorization_reusable"] is False
    assert record["resource_limits"]["maximum_persistent_mesh_write_batch"] == 0

    for payload in (auth, program):
        assert payload["authorization_transaction_id"] == record[
            "authorization_transaction_id"
        ]
        assert payload["approval_record_id"] == record["approval_record_id"]
        assert payload["candidate_id"] == record["candidate_id"]
        assert payload["workstream"] == record["workstream"]
        assert payload["implementation_task"] == record["implementation_task"]
        assert payload["formal_closeout_task"] == record["formal_closeout_task"]
        assert payload["active_knowledge_implementation_authorization_count"] == 1
        assert (
            payload["active_knowledge_implementation_authorization"]
            == "AION-212-KI-0005"
        )
        assert payload["active_knowledge_implementation_task"] == "AION-213"
        assert payload["active_cognitive_implementation_authorization_count"] == 0
        assert payload["domain_expert_mesh_authorized"] is True
        assert payload["domain_expert_mesh_implemented"] is False
        assert payload["domain_expert_mesh_runtime_enabled"] is False
        assert payload["persistent_expert_mesh_write_enabled"] is False


def test_aion_211_and_aion_212_program_rows_are_reconciled():
    records = {
        record["task_id"]: record
        for record in _program_ledger()["records"]
        if record["task_id"] in {"AION-211", "AION-212"}
    }
    assert set(records) == {"AION-211", "AION-212"}

    aion_211 = records["AION-211"]
    assert aion_211["authorization_state"] == "consumed_by_AION-211_closed_by_AION-212"
    assert aion_211["ci_result"] == "pass"
    assert aion_211["pull_requests"] == [123]
    assert aion_211["feature_commits"] == [
        "9a5bfca384a1720495cce677a817acef556f9e91"
    ]
    assert aion_211["merge_commits"] == [
        "737f166966aeacc2362fd62b852292264b3e2d97"
    ]
    assert (
        aion_211["runtime_state"]
        == "epistemic_truth_engine_implemented_in_memory_persistent_write_disabled"
    )

    aion_212 = records["AION-212"]
    assert aion_212["authorization_state"] == "active_for_AION-213_formal_closeout_AION-214"
    assert aion_212["authorization_transaction"] == "AION-212-KI-0005"
    assert aion_212["ci_result"] == "pass"
    assert aion_212["pull_requests"] == [124]
    assert aion_212["feature_commits"] == [
        "d3a92bc1626db5478e291900637f670e67c8819e",
        "2516118be9743fc6c4d7a26e656a1866d8ed7228",
        "11ce7f22be7e38918c069519d88f21a8020c0715",
    ]
    assert aion_212["merge_commits"] == [
        "70e40641dc2d3dad25e9b3dac4aff8405664b437"
    ]
    assert aion_212["next_task"] == "AION-213"
    assert aion_212["runtime_state"] == "domain_expert_mesh_authorized_not_implemented"
