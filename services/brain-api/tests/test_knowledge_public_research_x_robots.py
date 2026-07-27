from __future__ import annotations

from aion_brain.knowledge_intelligence.public_research_policy import evaluate_x_robots_header


def test_x_robots_noai_rejects() -> None:
    allowed, fingerprint = evaluate_x_robots_header(("noai",))
    assert allowed is False
    assert len(fingerprint) == 64
