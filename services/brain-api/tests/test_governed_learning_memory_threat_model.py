from __future__ import annotations

from test_governed_learning_memory_program_authorization import REPO_ROOT


def test_threat_model_preserves_candidate_truth_and_runtime_boundaries() -> None:
    threat_model = (REPO_ROOT / "docs/governed-learning-memory/threat-model.md").read_text(
        encoding="utf-8"
    )
    security_boundary = (
        REPO_ROOT / "docs/governed-learning-memory/security-boundary.md"
    ).read_text(encoding="utf-8")

    assert "Treating a verified candidate as durable truth" in threat_model
    assert "Treating operator approval as factual proof" in threat_model
    assert "Writing cognitive memory before a separate persistence authorization" in threat_model
    assert "Runtime activation remains false" in security_boundary
    assert "Operator approval authorizes a bounded transaction plan" in security_boundary
