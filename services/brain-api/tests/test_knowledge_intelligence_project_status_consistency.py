from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_project_status_current_state_matches_ledgers_and_retains_history() -> None:
    status = (REPO_ROOT / "docs/project-status.md").read_text(encoding="utf-8")
    ledger = json.loads(
        (REPO_ROOT / "docs/knowledge-intelligence/program-ledger.json").read_text(
            encoding="utf-8"
        )
    )
    assert ledger["active_knowledge_implementation_authorization"] in status
    assert ledger["active_knowledge_implementation_task"] in status
    assert ledger["formal_closeout_task"] in status
    assert "verified_knowledge_memory_implemented=true" in status
    assert "AION-209 compatibility marker" in status
    assert "AION-218 verified-knowledge memory operator evaluation complete" in status
