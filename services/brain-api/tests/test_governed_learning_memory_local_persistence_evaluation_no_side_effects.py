from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str):
    return json.loads((REPO_ROOT / relative).read_text())


def test_evaluation_report_records_zero_runtime_side_effects():
    report = load_json(
        "examples/governed-learning-memory/local-persistence-operator-evaluation-report.json"
    )
    for key in [
        "operator_local_stores_created",
        "production_memory_writes",
        "actual_belief_creations",
        "actual_belief_mutations",
        "automatic_knowledge_promotions",
        "engagement_learning_applications",
        "network_calls",
        "actual_tool_executions",
        "source_mutations",
        "git_operations",
    ]:
        assert report[key] == 0
    assert report["repository_unchanged"] is True
    assert report["temporary_evaluation_data_cleaned"] is True
