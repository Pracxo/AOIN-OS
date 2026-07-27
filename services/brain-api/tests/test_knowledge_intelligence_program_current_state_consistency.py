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


def test_current_status_matches_final_program_ledger() -> None:
    _require_final_closeout()
    status = (REPO_ROOT / "docs/project-status.md").read_text(encoding="utf-8")
    program = json.loads(
        (REPO_ROOT / "docs/knowledge-intelligence/program-ledger.json").read_text(
            encoding="utf-8"
        )
    )
    assert "AION-220 final Knowledge Intelligence Program evaluation and closeout complete" in status
    assert "The AION Knowledge Intelligence Program is complete." in status
    assert "knowledge_intelligence_program_complete=true" in status
    assert "controlled_public_research_pilot_passed=true" in status
    assert "active_knowledge_implementation_authorization_count=0" in status
    assert "active_knowledge_implementation_authorization=null" in status
    assert "next_knowledge_implementation_task=null" in status
    assert "v02_release_ready=false" in status
    assert program["program_state"] == "knowledge_intelligence_program_complete"
