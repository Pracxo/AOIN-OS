from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PUBLIC_RESEARCH_PILOT_STATE = (
    "controlled_public_research_pilot_authorized_not_implemented"
)


def load_json(relative: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def test_current_state_matches_active_aion218_authorization_and_status() -> None:
    program = load_json("docs/knowledge-intelligence/program-ledger.json")
    auth = load_json("docs/knowledge-intelligence/authorization-ledger.json")
    active = [item for item in auth["records"] if item.get("authorization_active") is True]
    assert len(active) == 1
    assert active[0]["authorization_transaction_id"] == "AION-218-KI-0008"
    for ledger in (program, auth):
        assert ledger["active_knowledge_implementation_authorization"] == "AION-218-KI-0008"
        assert ledger["active_knowledge_implementation_task"] == "AION-219"
        assert ledger["formal_closeout_task"] == "AION-220"
        assert ledger["program_state"] == PUBLIC_RESEARCH_PILOT_STATE
        assert ledger["controlled_public_research_pilot_authorized"] is True
        assert ledger["controlled_public_research_pilot_implemented"] is False
        assert ledger["public_network_fetch_enabled"] is False
    status = (REPO_ROOT / "docs/project-status.md").read_text(encoding="utf-8")
    assert "AION-218 verified-knowledge memory operator evaluation complete" in status
    assert "active_knowledge_implementation_authorization=AION-218-KI-0008" in status
    assert "active_knowledge_implementation_task=AION-219" in status
    assert "formal_closeout_task=AION-220" in status
