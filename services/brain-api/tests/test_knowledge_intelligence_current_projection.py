from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _load(relative: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def _active_record(ledger: dict[str, object]) -> dict[str, object]:
    records = ledger["records"]
    assert isinstance(records, list)
    active = [
        item
        for item in records
        if isinstance(item, dict) and item.get("authorization_transaction_id") == "AION-212-KI-0005"
    ]
    assert len(active) == 1
    return active[0]


def test_current_projection_matches_active_domain_expert_mesh_authorization() -> None:
    for relative in (
        "docs/knowledge-intelligence/authorization-ledger.json",
        "docs/knowledge-intelligence/program-ledger.json",
    ):
        ledger = _load(relative)
        active = _active_record(_load("docs/knowledge-intelligence/authorization-ledger.json"))
        assert ledger["authorization_transaction_id"] == active["authorization_transaction_id"]
        assert ledger["candidate_id"] == active["candidate_id"]
        assert ledger["workstream"] == active["workstream"]
        assert ledger["implementation_task"] == active["implementation_task"]
        assert ledger["formal_closeout_task"] == active["formal_closeout_task"]
        assert ledger["active_knowledge_implementation_authorization"] == "AION-212-KI-0005"
        assert ledger["active_knowledge_implementation_task"] == "AION-213"
        assert ledger["formal_closeout_task"] == "AION-214"
