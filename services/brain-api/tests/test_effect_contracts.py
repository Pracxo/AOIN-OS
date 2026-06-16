from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.effects import (
    ExpectedEffect,
    ExpectedEffectCreateRequest,
    ObservedEffect,
)


def test_expected_effect_validates_effect_type() -> None:
    with pytest.raises(ValidationError):
        ExpectedEffectCreateRequest(
            source_type="command",
            source_id="command-1",
            effect_type="domain_specific",  # type: ignore[arg-type]
            predicate="status",
            owner_scope=["workspace:main"],
        )


def test_expected_effect_rejects_empty_owner_scope() -> None:
    with pytest.raises(ValidationError):
        ExpectedEffect(
            expected_effect_id="expected-1",
            source_type="command",
            source_id="command-1",
            effect_type="generic",
            predicate="status",
            expected_value={},
            success_criteria={},
            required=True,
            confidence=0.5,
            owner_scope=[],
            evidence_refs=[],
            metadata={},
        )


def test_observed_effect_validates_observation_source_type() -> None:
    with pytest.raises(ValidationError):
        ObservedEffect(
            observed_effect_id="observed-1",
            source_type="command",
            source_id="command-1",
            effect_type="command_completed",
            predicate="status",
            observed_value={"status": "completed"},
            observation_source_type="invalid",  # type: ignore[arg-type]
            observation_source_id="command-1",
            confidence=0.5,
            sensitivity="internal",
            owner_scope=["workspace:main"],
            evidence_refs=[],
            belief_refs=[],
            situation_refs=[],
            metadata={},
            observed_at=datetime.now(UTC),
        )
