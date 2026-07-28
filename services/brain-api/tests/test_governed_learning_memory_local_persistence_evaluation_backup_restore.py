from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str):
    return json.loads((REPO_ROOT / relative).read_text())


def test_backup_and_restore_scenarios_record_integrity():
    report = load_json(
        "examples/governed-learning-memory/local-persistence-operator-evaluation-report.json"
    )
    backup = next(
        row for row in report["scenario_results"] if row["scenario_id"] == "backup_integrity"
    )
    restore = next(
        row
        for row in report["scenario_results"]
        if row["scenario_id"] == "restore_to_new_store_integrity"
    )
    assert backup["evidence"]["source_audit_before_backup"] is True
    assert backup["evidence"]["automatic_schedule"] is False
    assert restore["evidence"]["existing_store_overwritten"] is False
    assert restore["evidence"]["restored_logical_state_equal"] is True
