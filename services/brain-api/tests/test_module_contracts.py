"""Module runtime contract tests."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.modules import (
    CapabilityBindingRequest,
    CapabilityInvocationRequest,
    CapabilityRuntimeBinding,
    ModuleRuntime,
)


def test_module_runtime_validates_runtime_type() -> None:
    """ModuleRuntime rejects unknown runtime types."""
    with pytest.raises(ValidationError):
        ModuleRuntime(
            runtime_id="runtime-1",
            module_id="test.module",
            version="0.1.0",
            runtime_type="shell",
            endpoint_ref=None,
            status="registered",
            health_status="unknown",
            config={},
        )


def test_module_runtime_rejects_secret_like_config_keys() -> None:
    """Runtime config is metadata only and rejects secret keys recursively."""
    with pytest.raises(ValidationError):
        ModuleRuntime(
            runtime_id="runtime-1",
            module_id="test.module",
            version="0.1.0",
            runtime_type="local_internal",
            endpoint_ref=None,
            status="registered",
            health_status="unknown",
            config={"nested": {"token": "do-not-store"}},
        )


def test_capability_runtime_binding_validates_invocation_mode() -> None:
    """CapabilityRuntimeBinding rejects unknown invocation modes."""
    with pytest.raises(ValidationError):
        CapabilityRuntimeBinding(
            binding_id="binding-1",
            capability_id="aion.internal.noop",
            module_id="test.module",
            runtime_id="runtime-1",
            invocation_mode="external",
            status="active",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )


def test_capability_invocation_request_validates_mode() -> None:
    """CapabilityInvocationRequest rejects unknown modes."""
    with pytest.raises(ValidationError):
        CapabilityInvocationRequest(
            invocation_id="invocation-1",
            capability_id="aion.internal.noop",
            mode="external",
            payload={},
        )


def test_capability_binding_request_defaults_to_active() -> None:
    """CapabilityBindingRequest has an active binding default."""
    request = CapabilityBindingRequest(
        capability_id="aion.internal.noop",
        module_id="test.module",
        runtime_id="runtime-1",
        invocation_mode="dry_run",
    )

    assert request.status == "active"
