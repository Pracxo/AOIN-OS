from __future__ import annotations

import json
import os
from pathlib import Path

from scripts.lib import governed_learning_memory_local_persistence_operator_evaluation as eval225

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_operator_evaluation_harness_executes_all_scenarios(tmp_path: Path):
    output = tmp_path / "evaluation"
    output.mkdir()
    os.chmod(output, 0o700)
    report_path = output / "AION-GLMPE-002.json"

    report = eval225.run_evaluation(
        repo_root=REPO_ROOT,
        evaluation_id=eval225.EVALUATION_ID,
        evaluation_base_commit="test-base",
        temporary_output_directory=output,
        report_path=report_path,
    )

    assert report_path.exists()
    assert report["evaluation_id"] == "AION-GLMPE-002"
    assert report["decision"] == eval225.PASS_DECISION
    assert report["evaluation_passed"] is True
    assert report["scenario_count"] == 28
    assert tuple(report["scenario_ids"]) == eval225.SCENARIO_IDS
    assert [item["scenario_id"] for item in report["scenario_results"]] == list(
        eval225.SCENARIO_IDS
    )
    assert all(item["result"] == "passed" for item in report["scenario_results"])
    assert report["retained_database_files"] == 0
    assert report["retained_wal_files"] == 0
    assert report["retained_shm_files"] == 0
    assert report["retained_backup_files"] == 0
    assert report["retained_manifest_files"] == 0
    assert report["temporary_evaluation_data_cleaned"] is True
    assert not list(output.glob("*.sqlite3"))
    eval225.validate_evaluation_report(json.loads(report_path.read_text()))


def test_operator_evaluation_report_validator_rejects_missing_scenario(tmp_path: Path):
    report = {
        "evaluation_id": "AION-GLMPE-002",
        "scenario_count": 0,
        "scenario_ids": [],
        "scenario_results": [],
        "hard_gate_results": {},
        "decision": eval225.FAIL_DECISION,
        "evaluation_passed": False,
    }

    try:
        eval225.validate_evaluation_report(report)
    except eval225.EvaluationError as exc:
        assert "scenario" in str(exc)
    else:
        raise AssertionError("invalid report passed validation")
