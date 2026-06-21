from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.grounding import (
    GroundingSource,
    GroundingVerificationRequest,
    SourceCoverageReport,
)
from tests.grounding_helpers import source


def test_grounding_source_validates_trust_level_and_scope() -> None:
    record = source()
    assert record.trust_level == "primary"

    with pytest.raises(ValidationError):
        GroundingSource(**{**record.model_dump(), "owner_scope": []})

    with pytest.raises(ValidationError):
        GroundingSource(
            **{
                **record.model_dump(),
                "source_type": "memory",
                "trust_level": "primary",
            }
        )


def test_grounding_verification_request_requires_scope_and_target() -> None:
    with pytest.raises(ValidationError):
        GroundingVerificationRequest(target_type="response", owner_scope=[])

    with pytest.raises(ValidationError):
        GroundingVerificationRequest(target_type="response", owner_scope=["workspace:main"])


def test_source_coverage_report_validates_score() -> None:
    with pytest.raises(ValidationError):
        SourceCoverageReport(
            source_coverage_id="coverage-1",
            status="passed",
            owner_scope=["workspace:main"],
            coverage_score=1.5,
        )
