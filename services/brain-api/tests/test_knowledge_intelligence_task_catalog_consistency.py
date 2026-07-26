from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_task_catalog_summaries_match_program_records() -> None:
    ledger = json.loads(
        (REPO_ROOT / "docs/knowledge-intelligence/program-ledger.json").read_text(
            encoding="utf-8"
        )
    )
    records = {item["task_id"]: item for item in ledger["tasks"]}
    assert records["AION-213"]["evaluation_id"] == "AION-DEME-001"
    assert records["AION-214"]["authorization_transaction"] == "AION-214-KI-0006"
    assert records["AION-215"]["evaluation_id"] == "AION-IRAE-001"
    assert records["AION-216"]["authorization_transaction"] == "AION-216-KI-0007"
    assert records["AION-217"]["next_task"] == "AION-218"
