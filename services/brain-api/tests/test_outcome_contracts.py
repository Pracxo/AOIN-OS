from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.outcomes import (
    CausalAttribution,
    EffectVerificationRequest,
    OutcomeFeedback,
    OutcomeRecord,
)


def test_outcome_record_validates_score_bounds() -> None:
    with pytest.raises(ValidationError):
        OutcomeRecord(
            outcome_id="outcome-1",
            source_type="command",
            source_id="command-1",
            status="unknown",
            outcome_type="command",
            title="Outcome",
            summary="Summary",
            owner_scope=["workspace:main"],
            confidence=0.5,
            score=2.0,
            metadata={},
            observed_at=datetime.now(UTC),
        )


def test_effect_verification_request_rejects_empty_owner_scope() -> None:
    with pytest.raises(ValidationError):
        EffectVerificationRequest(source_id="command-1", owner_scope=[])


def test_causal_attribution_caused_requires_support() -> None:
    with pytest.raises(ValidationError):
        CausalAttribution(
            causal_attribution_id="cause-1",
            outcome_id="outcome-1",
            cause_type="command",
            cause_id="command-1",
            effect_type="observed_effect",
            effect_id="observed-1",
            relation_type="caused",
            confidence=0.8,
            evidence_refs=[],
            reasoning="No evidence.",
            metadata={},
        )


def test_outcome_feedback_rejects_empty_recommended_followup() -> None:
    with pytest.raises(ValidationError):
        OutcomeFeedback(
            outcome_feedback_id="feedback-1",
            source_type="outcome",
            source_id="outcome-1",
            feedback_type="missing_effect",
            status="open",
            severity="medium",
            message="Missing effect.",
            recommended_followup="",
            metadata={},
        )
