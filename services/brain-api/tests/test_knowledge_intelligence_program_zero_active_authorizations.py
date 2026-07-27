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


def test_zero_active_knowledge_authorizations_remain() -> None:
    _require_final_closeout()
    ledger = json.loads(
        (REPO_ROOT / "docs/knowledge-intelligence/authorization-ledger.json").read_text(
            encoding="utf-8"
        )
    )
    assert ledger["active_knowledge_implementation_authorization_count"] == 0
    assert ledger["active_knowledge_implementation_authorization"] is None
    assert ledger["active_knowledge_implementation_task"] is None
    assert [item for item in ledger["records"] if item.get("authorization_active") is True] == []
    assert all(item.get("authorization_reusable") is False for item in ledger["records"])
