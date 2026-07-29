from __future__ import annotations

import json
from pathlib import Path

from scripts.lib import governed_learning_memory_local_persistence_operator_evaluation as eval225

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str):
    return json.loads((REPO_ROOT / relative).read_text())


def test_evaluation_report_has_exact_scenarios():
    report = eval225.validate_evaluation_report_file(
        REPO_ROOT
        / "examples/governed-learning-memory/local-persistence-operator-evaluation-report.json"
    )
    assert tuple(report["scenario_ids"]) == eval225.SCENARIO_IDS
    assert report["scenario_count"] == 28
    assert all(item["result"] == "passed" for item in report["scenario_results"])
