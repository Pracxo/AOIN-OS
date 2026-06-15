"""Sandbox service tests."""

import pytest

from aion_brain.contracts.sandbox import SandboxRunRequest
from tests.sandbox_fakes import (
    FakePolicyAdapter,
    FakeTelemetry,
    make_sandbox_service,
    profile_request,
)


def test_sandbox_service_creates_profile_through_policy() -> None:
    policy = FakePolicyAdapter()
    telemetry = FakeTelemetry()
    service = make_sandbox_service(policy=policy, telemetry=telemetry)

    created = service.create_profile(profile_request())

    assert created.sandbox_profile_id == "sandbox-profile-1"
    assert policy.requests[0].action_type == "sandbox.profile.create"
    assert [event.event_type for event in telemetry.events] == ["sandbox_profile_created"]


def test_policy_deny_blocks_profile_creation() -> None:
    service = make_sandbox_service(policy=FakePolicyAdapter(allow=False))

    with pytest.raises(PermissionError):
        service.create_profile(profile_request())


def test_sandbox_service_dry_run_returns_no_code_executed() -> None:
    service = make_sandbox_service()
    service.create_profile(profile_request())

    result = service.run(
        SandboxRunRequest(
            sandbox_profile_id="sandbox-profile-1",
            target_type="capability",
            target_id="test.echo",
            mode="dry_run",
        )
    )

    assert result.status == "dry_run"
    assert result.output["module_code_executed"] is False
    assert result.output["external_calls"] is False


def test_sandbox_service_controlled_run_returns_unsupported_by_default() -> None:
    service = make_sandbox_service()
    service.create_profile(profile_request())

    result = service.run(
        SandboxRunRequest(
            sandbox_profile_id="sandbox-profile-1",
            target_type="capability",
            target_id="test.echo",
            mode="controlled",
            approval_present=True,
        )
    )

    assert result.status == "unsupported"
    assert result.error["reason"] == "sandbox_execution_disabled"
