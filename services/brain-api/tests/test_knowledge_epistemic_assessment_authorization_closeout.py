from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _authorization_records() -> list[dict]:
    payload = json.loads(
        (REPO_ROOT / "docs/knowledge-intelligence/authorization-ledger.json").read_text()
    )
    return payload["records"]


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
