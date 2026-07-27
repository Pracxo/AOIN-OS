from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_aion218_delivery_reconciliation_is_recorded() -> None:
    ledger = json.loads(
        (REPO_ROOT / "docs/knowledge-intelligence/program-ledger.json").read_text(encoding="utf-8")
    )
    records = ledger.get("records", [])
    aion218 = next((item for item in records if item.get("task_id") == "AION-218"), {})
    assert aion218.get("pull_requests") == [133]
    assert "a82dd6f8e9dd525456688defaae98587074860af" in aion218.get("merge_commits", [])
    assert aion218.get("corrective_prs") == [132]
