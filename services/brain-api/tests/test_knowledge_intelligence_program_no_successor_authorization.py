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


def test_no_successor_knowledge_authorization_or_aion221_is_created() -> None:
    _require_final_closeout()
    program = json.loads(
        (REPO_ROOT / "docs/knowledge-intelligence/program-ledger.json").read_text(
            encoding="utf-8"
        )
    )
    auth = json.loads(
        (REPO_ROOT / "docs/knowledge-intelligence/authorization-ledger.json").read_text(
            encoding="utf-8"
        )
    )
    assert program["new_knowledge_implementation_authorization_created"] is False
    assert program["next_knowledge_implementation_authorization"] is None
    assert program["next_knowledge_implementation_task"] is None
    assert auth["new_knowledge_implementation_authorization_created"] is False
    assert auth["next_knowledge_implementation_authorization"] is None
    assert auth["next_knowledge_implementation_task"] is None
    assert not any(item.get("task_id") == "AION-221" for item in program["records"])
