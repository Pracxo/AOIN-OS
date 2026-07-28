from __future__ import annotations

from pathlib import Path

from scripts.lib import governed_learning_memory_promotion_operator_evaluation as evaluation

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_evaluation_report_records_zero_runtime_write_and_repository_effects(
    tmp_path: Path,
) -> None:
    before = sorted(
        path.relative_to(REPO_ROOT).as_posix() for path in REPO_ROOT.rglob("*") if path.is_file()
    )
    report = evaluation.run_evaluation(
        repo_root=REPO_ROOT,
        evaluation_id=evaluation.EVALUATION_ID,
        evaluation_base_commit="unit-test-base",
        temporary_output_directory=tmp_path,
        report_path=tmp_path / "AION-GLMPE-001.json",
    )
    after = sorted(
        path.relative_to(REPO_ROOT).as_posix() for path in REPO_ROOT.rglob("*") if path.is_file()
    )

    assert before == after
    assert report["repository_unchanged"] is True
    for field in evaluation.ZERO_EFFECT_FIELDS:
        assert report[field] == 0
    assert report["runtime_state"]["local_persistence_implemented"] is False
    assert report["runtime_state"]["operator_invoked_persistence_available"] is False
