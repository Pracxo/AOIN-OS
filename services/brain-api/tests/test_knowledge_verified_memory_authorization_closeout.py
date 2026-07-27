from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def report() -> dict[str, object]:
    return load_json(
        "examples/knowledge-intelligence/verified-memory-operator-evaluation-report.json"
    )


def test_aion216_authorization_is_closed_and_non_reusable() -> None:
    ledger = load_json("docs/knowledge-intelligence/authorization-ledger.json")
    closed = [
        item
        for item in ledger["records"]
        if item.get("authorization_transaction_id") == "AION-216-KI-0007"
    ]
    assert len(closed) == 1
    record = closed[0]
    assert record["authorization_active"] is False
    assert record["authorization_consumed"] is True
    assert record["authorization_consumed_by_task"] == "AION-217"
    assert record["authorization_consumed_by_prs"] == [131, 132]
    assert record["authorization_expired"] is True
    assert record["authorization_reusable"] is False
    assert record["authorization_closed_by_task"] == "AION-218"
    assert record["verified_knowledge_memory_operator_evaluation_id"] == "AION-VKME-001"


def test_aion218_is_the_sole_active_knowledge_authorization() -> None:
    ledger = load_json("docs/knowledge-intelligence/authorization-ledger.json")
    active = [item for item in ledger["records"] if item.get("authorization_active") is True]
    if ledger["program_state"] == "knowledge_intelligence_program_complete":
        assert active == []
        record = next(
            item
            for item in ledger["records"]
            if item.get("authorization_transaction_id") == "AION-218-KI-0008"
        )
        assert record["authorization_active"] is False
        assert record["authorization_consumed"] is True
        assert record["authorization_consumed_by_task"] == "AION-219"
        assert record["authorization_expired"] is True
        assert record["authorization_reusable"] is False
        assert record["authorization_closed_by_task"] == "AION-220"
        return

    assert len(active) == 1
    record = active[0]
    assert record["authorization_transaction_id"] == "AION-218-KI-0008"
    assert record["implementation_task"] == "AION-219"
    assert record["formal_closeout_task"] == "AION-220"
    assert record["authorization_consumed"] is False
    assert record["authorization_expired"] is False
    assert record["authorization_reusable"] is False
