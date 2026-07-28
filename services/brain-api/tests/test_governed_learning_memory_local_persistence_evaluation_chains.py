from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str):
    return json.loads((REPO_ROOT / relative).read_text())


def test_chain_scenarios_record_hash_chain_integrity():
    report = load_json(
        "examples/governed-learning-memory/local-persistence-operator-evaluation-report.json"
    )
    global_chain = next(
        row
        for row in report["scenario_results"]
        if row["scenario_id"] == "global_ledger_hash_chain"
    )
    transaction_chain = next(
        row
        for row in report["scenario_results"]
        if row["scenario_id"] == "per_transaction_hash_chain_and_row_completeness"
    )
    assert global_chain["evidence"]["first_event_uses_zero_hash"] is True
    assert global_chain["evidence"]["global_sequence_contiguous"] is True
    assert transaction_chain["evidence"]["row_to_ledger_complete"] is True
