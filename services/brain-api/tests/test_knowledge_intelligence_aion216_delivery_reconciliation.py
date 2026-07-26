from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_aion216_delivery_reconciliation_is_exact() -> None:
    ledger = json.loads(
        (REPO_ROOT / "docs/knowledge-intelligence/program-ledger.json").read_text(
            encoding="utf-8"
        )
    )
    record = next(item for item in ledger["tasks"] if item["task_id"] == "AION-216")
    assert record["pull_requests"] == [130]
    assert record["merge_commits"] == ["368abd50cf99016d56158f68ac1c3f2465f50c26"]
    assert record["ci_result"] == "pass"
    assert record["authorization_transaction"] == "AION-216-KI-0007"
