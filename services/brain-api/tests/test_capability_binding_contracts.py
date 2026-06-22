"""Capability binding contract tests."""

import pytest
from pydantic import ValidationError

from aion_brain.contracts.capability_bindings import (
    CapabilityBindingCreateRequest,
    ModuleMountPlan,
    RouteBindingPreview,
)
from tests.module_binding_helpers import binding_request


def test_capability_binding_accepts_generic_metadata() -> None:
    request = binding_request("slot-1")

    assert request.capability_key == "test.echo.respond"
    assert request.target_runtime == "metadata_only"


def test_capability_binding_rejects_invalid_risk_level() -> None:
    with pytest.raises(ValidationError):
        binding_request("slot-1", risk_level="extreme")


def test_high_risk_binding_requires_approval() -> None:
    with pytest.raises(ValidationError):
        binding_request("slot-1", risk_level="high", requires_approval=False)


def test_controlled_binding_requires_sandbox() -> None:
    with pytest.raises(ValidationError):
        CapabilityBindingCreateRequest.model_validate(
            {
                "module_slot_id": "slot-1",
                "capability_key": "test.echo.respond",
                "controlled_supported": True,
                "requires_sandbox": False,
            }
        )


def test_mount_plan_must_not_execute() -> None:
    with pytest.raises(ValidationError):
        ModuleMountPlan(
            mount_plan_id="plan-1",
            module_slot_id="slot-1",
            status="blocked",
            plan_type="mount_preview",
            owner_scope=["workspace:main"],
            blocked=True,
            executable=True,
            execution_allowed=False,
        )


def test_route_preview_must_not_register() -> None:
    with pytest.raises(ValidationError):
        RouteBindingPreview(
            route_preview_id="route-1",
            status="blocked",
            route_key="test.echo.respond",
            route_type="generic",
            target_runtime="metadata_only",
            would_register=True,
            registration_allowed=True,
        )
