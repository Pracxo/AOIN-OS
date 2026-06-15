"""Autonomy contract tests."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.autonomy import (
    AutonomyDecisionRequest,
    AutonomyProfileCreateRequest,
    DelegationGrantRequest,
    SetRunLevelRequest,
)


def test_autonomy_profile_defaults_are_conservative() -> None:
    """The default profile request is assist-only with dry-run as its ceiling."""
    request = AutonomyProfileCreateRequest(
        name="Default",
        description="Default generic autonomy profile.",
    )

    assert request.default_mode == "assist"
    assert request.max_mode == "dry_run"
    assert request.max_risk_level == "medium"
    assert request.external_models_allowed is False
    assert request.external_tools_allowed is False
    assert request.background_workflows_allowed is False


def test_autonomy_contracts_reject_domain_terms() -> None:
    """Autonomy contracts stay generic and domain-neutral."""
    with pytest.raises(ValidationError):
        AutonomyDecisionRequest(
            requested_mode="dry_run",
            action_type="finance.trade",
            resource_type="capability",
            risk_level="low",
        )


def test_autonomy_contracts_reject_secret_like_payloads() -> None:
    """Autonomy metadata must not carry secret-like keys."""
    with pytest.raises(ValidationError):
        AutonomyDecisionRequest(
            requested_mode="dry_run",
            action_type="capability.invoke",
            resource_type="capability",
            risk_level="low",
            metadata={"api_key": "hidden"},
        )


def test_delegation_requires_controlled_mode() -> None:
    """Delegations only cover bounded controlled modes."""
    with pytest.raises(ValidationError):
        DelegationGrantRequest(reason="generic delegation", mode="assist")


def test_run_level_validates_explicit_mode() -> None:
    """Run levels use the shared autonomy mode vocabulary."""
    record = SetRunLevelRequest(
        run_level="observe",
        reason="observe while testing",
        expires_at=datetime.now(UTC),
    )

    assert record.run_level == "observe"
