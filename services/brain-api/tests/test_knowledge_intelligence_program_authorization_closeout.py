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


def test_aion218_ki_0008_is_closed_by_aion220_after_program_closeout() -> None:
    _require_final_closeout()
    ledger = json.loads(
        (REPO_ROOT / "docs/knowledge-intelligence/authorization-ledger.json").read_text(
            encoding="utf-8"
        )
    )
    record = next(
        item
        for item in ledger["records"]
        if item.get("authorization_transaction_id") == "AION-218-KI-0008"
    )
    assert record["authorization_active"] is False
    assert record["authorization_consumed"] is True
    assert record["authorization_consumed_by_task"] == "AION-219"
    assert record["authorization_consumed_by_prs"] == [134]
    assert record["authorization_consumed_by_feature_commits"] == [
        "756c706299472d6f048acd4a2c6a523c36f0e119"
    ]
    assert record["authorization_consumed_by_merge_commits"] == [
        "d0e1807edd7b3098ce62f8d00b0bceb4ee6fd23d"
    ]
    assert record["authorization_expired"] is True
    assert record["authorization_reusable"] is False
    assert record["authorization_closed_by_task"] == "AION-220"
