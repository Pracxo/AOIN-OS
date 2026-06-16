"""Cognitive cycle contract tests."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.config import Settings
from aion_brain.contracts.cycles import (
    CognitiveCycleRunRequest,
    CognitiveCycleStep,
    CognitiveCycleTemplate,
    SleepConsolidationRequest,
)


def test_cycle_contracts_accept_generic_template() -> None:
    """Generic cycle templates validate."""
    template = CognitiveCycleTemplate(
        cycle_template_id="template-1",
        name="Generic cycle",
        description="Review local Brain state.",
        cycle_type="review",
        status="active",
        owner_scope=["workspace:main"],
        steps=[
            CognitiveCycleStep(
                step_id="step-1",
                step_type="noop",
                description="No operation.",
            )
        ],
        risk_level="low",
        requires_approval=False,
        metadata={},
        created_at=datetime.now(UTC),
    )

    assert template.cycle_type == "review"
    assert template.steps[0].step_type == "noop"


def test_cycle_contract_rejects_empty_scope() -> None:
    """Cycle templates require an owner scope."""
    with pytest.raises(ValidationError):
        CognitiveCycleTemplate(
            cycle_template_id="template-1",
            name="Generic cycle",
            description="Review local Brain state.",
            cycle_type="review",
            status="active",
            owner_scope=[],
            steps=[
                CognitiveCycleStep(
                    step_id="step-1",
                    step_type="noop",
                    description="No operation.",
                )
            ],
            risk_level="low",
            requires_approval=False,
        )


def test_cycle_contract_rejects_secret_like_payloads() -> None:
    """Cycle inputs must not store secret-like keys."""
    with pytest.raises(ValidationError):
        CognitiveCycleRunRequest(
            cycle_type="sleep_consolidation",
            owner_scope=["workspace:main"],
            input={"api_key": "redacted"},
        )


def test_cycle_contract_rejects_domain_terms() -> None:
    """Cycle templates stay domain-neutral."""
    with pytest.raises(ValidationError):
        CognitiveCycleTemplate(
            cycle_template_id="template-1",
            name="Trading cycle",
            description="Review local Brain state.",
            cycle_type="review",
            status="active",
            owner_scope=["workspace:main"],
            steps=[
                CognitiveCycleStep(
                    step_id="step-1",
                    step_type="noop",
                    description="No operation.",
                )
            ],
            risk_level="low",
            requires_approval=False,
        )


def test_sleep_consolidation_request_defaults_to_dry_run() -> None:
    """Sleep consolidation defaults to dry-run mode."""
    request = SleepConsolidationRequest()

    assert request.mode == "dry_run"
    assert request.scope == []


def test_cycle_settings_defaults_are_safe() -> None:
    """Cognitive cycle settings keep automatic execution disabled."""
    settings = Settings()

    assert settings.cognitive_cycles_enabled is True
    assert settings.sleep_consolidation_enabled is True
    assert settings.cycle_controlled_mode_requires_approval is True
    assert settings.cycle_auto_run_enabled is False
