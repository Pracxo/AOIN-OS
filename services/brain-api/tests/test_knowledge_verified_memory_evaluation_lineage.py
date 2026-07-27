from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def report() -> dict[str, object]:
    return load_json(
        "examples/knowledge-intelligence/verified-memory-operator-evaluation-report.json"
    )


def test_lineage_scenario_and_gate_passed() -> None:
    data = report()
    scenarios = {item["scenario_id"]: item for item in data["scenario_results"]}
    assert scenarios["integrated_lineage_integrity"]["passed"] is True
    assert data["hard_gate_results"]["lineage_integrity_passed"] is True
    assert data["repository_integrity"]["runtime_source_changed"] is False
    assert data["corrective_prs"] == [132]
