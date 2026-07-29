from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_threat_model_keeps_autonomy_and_production_effects_out_of_scope() -> None:
    text = (
        REPO_ROOT / "docs/governed-learning-memory/continual-learning-threat-model.md"
    ).read_text(encoding="utf-8")
    for phrase in (
        "engagement treated as factual evidence",
        "unrestricted source discovery",
        "automatic continuation",
        "belief mutation",
        "model training",
        "authorization reuse",
    ):
        assert phrase in text
