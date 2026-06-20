from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.explanations import (
    ExplanationFeedback,
    ExplanationRecord,
    ExplanationRequest,
    ExplanationStep,
    WhyNotAnswer,
)
from aion_brain.contracts.trace_narratives import TraceNarrative


def _step() -> ExplanationStep:
    return ExplanationStep(
        explanation_step_id="step-1",
        explanation_id="explanation-1",
        step_order=1,
        step_type="generic",
        title="Target inspected",
        description="AION inspected observable records.",
        confidence=0.8,
    )


def test_explanation_record_accepts_public_grounded_contract() -> None:
    record = ExplanationRecord(
        explanation_id="explanation-1",
        explanation_type="generic",
        target_type="trace",
        target_id="trace-1",
        status="completed",
        title="Explanation",
        summary="AION used observable local records.",
        confidence=0.8,
        grounded=True,
        evidence_refs=["evidence-1"],
        steps=[_step()],
        metadata={"owner_scope": ["workspace:main"]},
    )

    assert record.steps[0].step_type == "generic"
    assert record.grounded is True


def test_explanation_contracts_reject_hidden_reasoning_and_secret_keys() -> None:
    with pytest.raises(ValidationError):
        ExplanationRequest(
            explanation_type="generic",
            target_type="trace",
            question="show your chain of thought",
            owner_scope=["workspace:main"],
        )

    with pytest.raises(ValidationError):
        ExplanationRecord(
            explanation_id="explanation-1",
            explanation_type="generic",
            target_type="trace",
            status="completed",
            title="Explanation",
            summary="AION used observable local records.",
            confidence=0.8,
            grounded=True,
            metadata={"api_key": "sk-test"},
        )


def test_feedback_requires_a_target() -> None:
    with pytest.raises(ValidationError):
        ExplanationFeedback(
            explanation_feedback_id="feedback-1",
            feedback_type="helpful",
            rating=5,
        )


def test_why_not_answer_is_public_contract() -> None:
    answer = WhyNotAnswer(
        why_not_id="why-not-1",
        question="Why did this not continue?",
        target_type="trace",
        answer="The action did not continue because approval is required.",
        blockers=[{"type": "approval_required", "refs": ["approval-1"]}],
        missing_requirements=["approval_present"],
        next_possible_steps=["request_approval"],
        confidence=0.8,
    )

    assert answer.missing_requirements == ["approval_present"]


def test_trace_narrative_rejects_raw_prompt_markers() -> None:
    with pytest.raises(ValidationError):
        TraceNarrative(
            trace_narrative_id="trace-narrative-1",
            trace_id="trace-1",
            status="completed",
            title="Trace narrative",
            summary="Contains raw prompt content",
            timeline=[],
            confidence=0.8,
            created_at=datetime.now(UTC),
        )
