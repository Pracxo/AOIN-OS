from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str):
    return json.loads((REPO_ROOT / relative).read_text())


def test_atomicity_scenario_records_begin_immediate_and_rollback_boundary():
    report = load_json(
        "examples/governed-learning-memory/local-persistence-operator-evaluation-report.json"
    )
    item = next(
        row
        for row in report["scenario_results"]
        if row["scenario_id"] == "atomic_transaction_commit_and_rollback"
    )
    assert item["evidence"]["begin_immediate_used"] is True
    assert item["evidence"]["rows_and_ledger_commit_together"] is True
    assert item["evidence"]["no_partial_receipt"] is True
