"""Conformance contract tests."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.conformance import (
    CapabilityTestVectorCreateRequest,
    ConformanceProfileCreateRequest,
)
from aion_brain.contracts.readiness import ReadinessAssessment


def test_conformance_profile_rejects_domain_terms() -> None:
    with pytest.raises(ValidationError):
        ConformanceProfileCreateRequest(
            name="finance profile",
            description="Generic profile.",
            owner_scope=["workspace:main"],
        )


def test_test_vector_rejects_executable_payload_fields() -> None:
    with pytest.raises(ValidationError):
        CapabilityTestVectorCreateRequest(
            name="Unsafe vector",
            description="Generic test vector.",
            input_payload={"command": "run"},
            owner_scope=["workspace:main"],
        )


def test_readiness_assessment_never_allows_activation_ready_true() -> None:
    with pytest.raises(ValidationError):
        ReadinessAssessment(
            readiness_assessment_id="readiness-1",
            status="ready",
            readiness_level="conformant",
            activation_ready=True,
            minimum_score=0.8,
            actual_score=1.0,
            owner_scope=["workspace:main"],
            created_at=datetime.now(UTC),
        )
