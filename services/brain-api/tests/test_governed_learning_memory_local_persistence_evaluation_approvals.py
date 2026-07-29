from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str):
    return json.loads((REPO_ROOT / relative).read_text())


def test_approval_scenarios_record_dual_approval_and_binding():
    report = load_json(
        "examples/governed-learning-memory/local-persistence-operator-evaluation-report.json"
    )
    dual = next(
        row
        for row in report["scenario_results"]
        if row["scenario_id"] == "dual_persistence_approval"
    )
    binding = next(
        row for row in report["scenario_results"] if row["scenario_id"] == "exact_approval_binding"
    )
    assert dual["evidence"]["independent_approver_count"] == 2
    assert dual["evidence"]["runtime_creates_no_approval"] is True
    assert binding["evidence"]["changed_binding_fails_closed"] is True
