from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
FINAL_REPORT = (
    REPO_ROOT
    / "examples/knowledge-intelligence/knowledge-intelligence-program-final-evaluation-report.json"
)


def _require_final_closeout() -> None:
    if not FINAL_REPORT.exists():
        pytest.skip("AION-220 final closeout evidence is not committed yet")


def test_knowledge_intelligence_program_complete_state_is_recorded() -> None:
    _require_final_closeout()
    program = json.loads(
        (REPO_ROOT / "docs/knowledge-intelligence/program-ledger.json").read_text(
            encoding="utf-8"
        )
    )
    assert program["program_state"] == "knowledge_intelligence_program_complete"
    assert program["knowledge_intelligence_program_complete"] is True
    assert program["knowledge_intelligence_program_evaluation_id"] == "AION-KIPE-001"
    assert (
        program["knowledge_intelligence_program_evaluation_decision"]
        == "CONTROLLED_PUBLIC_RESEARCH_PILOT_PASS_COMPLETE_KNOWLEDGE_INTELLIGENCE_PROGRAM"
    )
    assert program["controlled_public_research_pilot_passed"] is True
    assert program["active_knowledge_implementation_authorization_count"] == 0
    assert program["active_knowledge_implementation_authorization"] is None
    assert program["active_knowledge_implementation_task"] is None
    assert program["formal_closeout_task"] is None
    assert program["next_knowledge_implementation_authorization"] is None
    assert program["next_knowledge_implementation_task"] is None
    assert program["v02_release_ready"] is False
