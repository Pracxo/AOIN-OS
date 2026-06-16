from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.beliefs.confidence import score_belief_confidence
from aion_brain.contracts.beliefs import BeliefContradiction, BeliefSupport


def test_confidence_scorer_increases_with_evidence_support() -> None:
    support = BeliefSupport(
        support_id="support-1",
        claim_id="claim-1",
        support_type="evidence",
        source_type="evidence",
        source_id="evidence-1",
        relation_type="supports",
        strength=0.8,
        confidence=0.8,
        created_at=datetime.now(UTC),
    )

    score = score_belief_confidence(0.5, [support], [], ["evidence-1"], [], "evidence")

    assert score > 0.5


def test_confidence_scorer_decreases_with_contradiction() -> None:
    contradiction = BeliefContradiction(
        contradiction_id="contradiction-1",
        claim_id="claim-1",
        source_type="generic",
        source_id="source-1",
        contradiction_type="generic",
        severity="high",
        status="open",
        reason="conflict",
        created_at=datetime.now(UTC),
    )

    score = score_belief_confidence(0.8, [], [contradiction], [], [], "generic")

    assert score < 0.8
