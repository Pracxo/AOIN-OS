"""Module activation contract tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.module_activation import (
    ActivationBlocker,
    ActivationGateRun,
    ActivationPlan,
    ModuleActivationCreateRequest,
    ModuleActivationRequest,
    RuntimeRegistrationPreview,
)


def test_activation_request_never_allows_activation() -> None:
    with pytest.raises(ValidationError):
        ModuleActivationRequest(
            activation_request_id="activation-request-1",
            module_slot_id="slot-1",
            status="requested",
            request_type="future_activation",
            activation_target="module_slot",
            requested_mode="dry_run",
            risk_level="medium",
            owner_scope=["workspace:main"],
            activation_allowed=True,
            execution_allowed=False,
        )


def test_create_request_rejects_secret_payload() -> None:
    with pytest.raises(ValidationError):
        ModuleActivationCreateRequest(
            module_slot_id="slot-1",
            owner_scope=["workspace:main"],
            metadata={"api_key": "secret"},
        )


def test_gate_plan_and_preview_are_non_executable() -> None:
    blocker = ActivationBlocker(
        activation_blocker_id="blocker-1",
        blocker_type="activation_disabled",
        severity="critical",
        status="open",
        reason="Activation disabled.",
        recommended_action="Keep request metadata-only.",
    )
    gate = ActivationGateRun(
        activation_gate_run_id="gate-1",
        activation_request_id="request-1",
        status="blocked",
        mode="dry_run",
        owner_scope=["workspace:main"],
        blockers=[blocker],
        score=0.0,
        activation_allowed=False,
    )
    plan = ActivationPlan(
        activation_plan_id="plan-1",
        activation_request_id="request-1",
        module_slot_id="slot-1",
        status="blocked",
        plan_type="future_activation",
        owner_scope=["workspace:main"],
        blocked=True,
        executable=False,
        execution_allowed=False,
    )
    preview = RuntimeRegistrationPreview(
        registration_preview_id="preview-1",
        status="blocked",
        preview_type="module_runtime",
        target_runtime="metadata_only",
        would_register=False,
        registration_allowed=False,
    )

    assert gate.activation_allowed is False
    assert plan.executable is False
    assert preview.registration_allowed is False
