from __future__ import annotations

from scripts.lib import governed_learning_memory_promotion_operator_evaluation as evaluation
from test_governed_learning_memory_program_authorization import REPO_ROOT, load_json


def test_evaluation_report_artifact_is_valid_and_immutable() -> None:
    report = evaluation.validate_evaluation_report_file(
        REPO_ROOT / "examples/governed-learning-memory/promotion-operator-evaluation-report.json"
    )
    assert report["evaluation_id"] == "AION-GLMPE-001"
    assert report["decision"] == evaluation.PASS_DECISION
    assert report["scenario_count"] == 28
    assert (
        report["synthetic"] is True and report["read_only"] is True and report["redacted"] is True
    )
    assert report["security_state"]["protected_material_absent"] is True


def test_required_evaluation_documents_exist() -> None:
    required = [
        "docs/governed-learning-memory/promotion-operator-evaluation-closeout.md",
        "docs/governed-learning-memory/promotion-operator-evaluation-report.md",
        "docs/governed-learning-memory/promotion-evaluation-scenarios.md",
        "docs/governed-learning-memory/promotion-evaluation-security-boundary.md",
        "docs/release/governed-learning-memory-promotion-evaluation-closeout.md",
        "docs/release/governed-learning-memory-promotion-evaluation-checklist.md",
        "docs/release/governed-learning-memory-promotion-evaluation-evidence-matrix.md",
        "docs/release/governed-learning-memory-promotion-evaluation-runtime-hold.md",
        "docs/adr/0187-promotion-transaction-evaluation-and-local-append-only-knowledge-persistence-authorization.md",
    ]
    for rel in required:
        assert (REPO_ROOT / rel).is_file(), rel
    assert (
        load_json(
            "operator-console-static/demo-data/governed-learning-memory-promotion-evaluation.json"
        )["scenario_count"]
        == 28
    )
