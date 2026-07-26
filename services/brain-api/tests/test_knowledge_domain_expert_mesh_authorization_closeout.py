from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PASS_DECISION = (
    "DOMAIN_EXPERT_MESH_OPERATOR_EVALUATION_PASS_RECOMMEND_"
    "TOOL_VERIFICATION_FABRIC_AUTHORIZATION"
)


def _load(relative: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def _auth_records() -> list[dict[str, object]]:
    records = _load("docs/knowledge-intelligence/authorization-ledger.json")["records"]
    assert isinstance(records, list)
    return [item for item in records if isinstance(item, dict)]


def test_aion_212_ki_0005_is_closed_and_non_reusable() -> None:
    records = [
        item
        for item in _auth_records()
        if item.get("authorization_transaction_id") == "AION-212-KI-0005"
    ]
    assert len(records) == 1
    record = records[0]

    assert record["authorization_active"] is False
    assert record["authorization_consumed"] is True
    assert record["authorization_expired"] is True
    assert record["authorization_reusable"] is False
    assert record["authorization_consumed_by_task"] == "AION-213"
    assert record["authorization_consumed_by_prs"] == [127]
    assert record["authorization_consumed_by_feature_commits"] == [
        "ab7ef61ad45b484ead47d3338e6fd8ea13b3bdbe"
    ]
    assert record["authorization_consumed_by_merge_commits"] == [
        "99ce337a99f7f5eb98081b86fa735dd03582800e"
    ]
    assert record["authorization_closed_by_task"] == "AION-214"
    assert record["domain_expert_mesh_operator_evaluation_id"] == "AION-DEME-001"
    assert record["domain_expert_mesh_operator_evaluation_decision"] == PASS_DECISION
    assert record["evaluation_used_as_approval"] is False


def test_only_aion_214_ki_0006_is_active_after_closeout() -> None:
    active = [item for item in _auth_records() if item.get("authorization_active") is True]
    assert [item["authorization_transaction_id"] for item in active] == ["AION-214-KI-0006"]
