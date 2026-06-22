"""Skill contract tests."""

import pytest
from pydantic import ValidationError

from aion_brain.contracts.skills import (
    SkillCandidate,
    SkillMatchRequest,
    SkillProcedureStep,
    SkillRecord,
)


def test_skill_procedure_step_validates_risk_level() -> None:
    """SkillProcedureStep accepts only generic risk levels."""
    with pytest.raises(ValidationError):
        SkillProcedureStep(
            step_id="step-1",
            action_type="retrieve_context",
            description="Retrieve context",
            risk_level="domain-risk",
        )


def test_skill_candidate_rejects_empty_procedure_steps() -> None:
    """Skill candidates require data-only procedure steps."""
    with pytest.raises(ValidationError):
        SkillCandidate(
            candidate_id="candidate-1",
            source_trace_ids=["trace-1"],
            name="Generic procedure",
            description="Generic procedure description",
            trigger_patterns=["question.answer"],
            procedure_steps=[],
            risk_level="medium",
            confidence=0.7,
            status="candidate",
        )


def test_skill_record_rejects_empty_owner_scope() -> None:
    """Skill records require an owner scope."""
    with pytest.raises(ValidationError):
        SkillRecord(
            skill_id="skill-1",
            name="Generic procedure",
            description="Generic procedure description",
            status="draft",
            risk_level="medium",
            current_version=1,
            trigger_patterns=["question.answer"],
            procedure_steps=[make_step()],
            owner_scope=[],
        )


def test_skill_match_request_validates_scope_and_limit() -> None:
    """SkillMatchRequest bounds scope and limit."""
    with pytest.raises(ValidationError):
        SkillMatchRequest(query="generic", scope=[], limit=10)
    with pytest.raises(ValidationError):
        SkillMatchRequest(query="generic", scope=["workspace:main"], limit=100)


def test_skill_contracts_reject_domain_specific_terms() -> None:
    """Brain core skill contracts reject vertical terms."""
    with pytest.raises(ValidationError):
        SkillCandidate(
            candidate_id="candidate-1",
            source_trace_ids=["trace-1"],
            name="Finance procedure",
            description="Generic procedure description",
            trigger_patterns=["question.answer"],
            procedure_steps=[make_step()],
            risk_level="medium",
            confidence=0.7,
            status="candidate",
        )


def make_step() -> SkillProcedureStep:
    """Create a generic skill step."""
    return SkillProcedureStep(
        step_id="step-1",
        action_type="retrieve_context",
        description="Retrieve context",
        risk_level="low",
    )
