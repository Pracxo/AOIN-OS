from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str):
    return json.loads((REPO_ROOT / relative).read_text())


def test_projection_scenarios_keep_memory_and_belief_boundaries():
    report = load_json(
        "examples/governed-learning-memory/local-persistence-operator-evaluation-report.json"
    )
    semantic = next(
        row
        for row in report["scenario_results"]
        if row["scenario_id"] == "semantic_projection_isolation"
    )
    belief = next(
        row
        for row in report["scenario_results"]
        if row["scenario_id"] == "belief_candidate_boundary"
    )
    assert semantic["evidence"]["semantic_record_count"] == 1
    assert semantic["evidence"]["memory_repository_unused"] is True
    assert belief["evidence"]["actual_belief_created"] is False
    assert belief["evidence"]["BeliefClaim_absent"] is True
