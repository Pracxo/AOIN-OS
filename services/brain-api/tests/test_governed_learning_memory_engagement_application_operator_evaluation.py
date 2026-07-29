from __future__ import annotations

import json
from pathlib import Path

from scripts.lib import (
    governed_learning_memory_engagement_application_operator_evaluation as eval227,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_operator_evaluation_harness_executes_all_scenarios(tmp_path: Path):
    report_path = tmp_path / "AION-GLMPE-003.json"

    report = eval227.run_evaluation(
        repo_root=REPO_ROOT,
        evaluation_id=eval227.EVALUATION_ID,
        evaluation_base_commit="unit-test-base",
        temporary_output_directory=tmp_path,
        report_path=report_path,
    )

    assert report_path.exists()
    assert report["evaluation_id"] == "AION-GLMPE-003"
    assert report["scenario_count"] == 28
    assert report["scenario_ids"] == list(eval227.SCENARIO_IDS)
    assert [item["scenario_id"] for item in report["scenario_results"]] == list(
        eval227.SCENARIO_IDS
    )
    assert all(item["result"] in {"passed", "failed"} for item in report["scenario_results"])
    assert report["decision"] in {eval227.PASS_DECISION, eval227.FAIL_DECISION}
    assert report["synthetic"] is True
    assert report["read_only"] is True
    assert report["redacted"] is True
    assert report["repository_unchanged"] is True
    assert report["temporary_evaluation_data_cleaned"] is True
    eval227.validate_evaluation_report(json.loads(report_path.read_text()))


def test_operator_evaluation_report_validator_rejects_manual_pass_upgrade():
    report = {
        "evaluation_id": eval227.EVALUATION_ID,
        "scenario_count": 28,
        "scenario_ids": list(eval227.SCENARIO_IDS),
        "scenario_results": [
            {"scenario_id": scenario_id, "result": "passed", "checks": {}}
            for scenario_id in eval227.SCENARIO_IDS
        ],
        "hard_gate_results": {
            gate: {"result": "passed", "passed": True}
            for gate in eval227.HARD_GATE_IDS
        },
        "decision": eval227.PASS_DECISION,
        "evaluation_passed": True,
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "repository_unchanged": True,
        "temporary_evaluation_data_cleaned": True,
        "report_fingerprint": "0" * 64,
    }
    report["scenario_results"][0]["result"] = "failed"

    try:
        eval227.validate_evaluation_report(report)
    except eval227.EvaluationError as exc:
        assert "decision" in str(exc)
    else:
        raise AssertionError("manual PASS upgrade was accepted")
