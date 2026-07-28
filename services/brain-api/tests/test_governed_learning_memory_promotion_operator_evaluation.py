from __future__ import annotations

from pathlib import Path

from scripts.lib import governed_learning_memory_promotion_operator_evaluation as evaluation

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_promotion_operator_evaluation_runs_all_scenarios(tmp_path: Path) -> None:
    report_path = tmp_path / "AION-GLMPE-001.json"

    report = evaluation.run_evaluation(
        repo_root=REPO_ROOT,
        evaluation_id=evaluation.EVALUATION_ID,
        evaluation_base_commit="unit-test-base",
        temporary_output_directory=tmp_path,
        report_path=report_path,
    )

    assert report_path.is_file()
    assert report["evaluation_id"] == "AION-GLMPE-001"
    assert report["decision"] == evaluation.PASS_DECISION
    assert report["evaluation_passed"] is True
    assert report["scenario_count"] == 28
    assert [item["scenario_id"] for item in report["scenario_results"]] == list(
        evaluation.REQUIRED_SCENARIO_IDS
    )
    assert all(item["result"] == "passed" for item in report["scenario_results"])
    evaluation.validate_evaluation_report_file(report_path)


def test_promotion_operator_evaluation_uses_expected_aion222_delivery() -> None:
    report = evaluation.build_report(
        evaluation_id=evaluation.EVALUATION_ID,
        evaluation_base_commit=evaluation.AION_222_MERGE_COMMIT,
        tmp_dir=Path("/tmp/aion-glm-promotion-evaluation-test"),
    )

    assert report["implementation_prs"] == [138]
    assert report["implementation_feature_commits"] == ["e415cc397b9aec70f8b3d19285f5fdd315048731"]
    assert report["implementation_merge_commits"] == ["b89c896b8e75955d28fd06d52b5fb66fb8ed5ac0"]
    assert report["authorization_closeout"]["authorization_transaction_id"] == ("AION-221-GLM-0001")
    assert report["conditional_next_authorization"]["authorization_transaction_id"] == (
        "AION-223-GLM-0002"
    )
