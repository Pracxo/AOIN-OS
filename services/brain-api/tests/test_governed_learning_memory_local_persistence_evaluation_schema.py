from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str):
    return json.loads((REPO_ROOT / relative).read_text())


def test_schema_scenario_records_schema_identity():
    report = load_json(
        "examples/governed-learning-memory/local-persistence-operator-evaluation-report.json"
    )
    item = next(
        row
        for row in report["scenario_results"]
        if row["scenario_id"] == "schema_identity_and_object_set"
    )
    assert item["evidence"]["application_id"] == 223224
    assert item["evidence"]["user_version"] == 1
    assert item["evidence"]["table_count"] == 9
    assert item["evidence"]["trigger_count"] == 18
