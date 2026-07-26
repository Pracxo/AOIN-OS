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
        if isinstance(item, dict) and item.get("authorization_transaction_id") == "AION-214-KI-0006"
    ]
    assert len(active) == 1
    return active[0]


def test_current_projection_matches_active_tool_verification_authorization() -> None:
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
        assert ledger["active_knowledge_implementation_authorization"] == "AION-214-KI-0006"
        assert ledger["active_knowledge_implementation_task"] == "AION-215"
        assert ledger["formal_closeout_task"] == "AION-216"
        assert ledger["tool_verification_fabric_authorized"] is True
        assert ledger["tool_verification_fabric_implemented"] is True
        assert ledger["tool_verification_fabric_state"] == (
            "implemented_deterministic_simulation_verification_attestation_persistent_write_disabled"
        )
        assert ledger["tool_verification_fabric_runtime_enabled"] is False
        assert ledger["actual_tool_execution_enabled"] is False
        assert ledger["persistent_tool_state_write_enabled"] is False


def test_aion_212_authorization_is_closed_after_domain_mesh_evaluation() -> None:
    ledger = _load("docs/knowledge-intelligence/authorization-ledger.json")
    records = ledger["records"]
    assert isinstance(records, list)
    closed = [
        item
        for item in records
        if isinstance(item, dict) and item.get("authorization_transaction_id") == "AION-212-KI-0005"
    ]
    assert len(closed) == 1
    assert closed[0]["authorization_active"] is False
    assert closed[0]["authorization_consumed"] is True
    assert closed[0]["authorization_expired"] is True
    assert closed[0]["authorization_reusable"] is False
