"""HTTP runtime placeholder tests."""

import pytest

from aion_brain.contracts.modules import CapabilityInvocationRequest, ModuleRuntime
from aion_brain.modules.http_runtime import HttpRuntimeAdapter


def test_http_runtime_placeholder_raises_not_implemented() -> None:
    """HTTP runtime does not perform network calls in v0.1."""
    adapter = HttpRuntimeAdapter()

    with pytest.raises(NotImplementedError):
        adapter.health_check(runtime().model_copy(update={"runtime_type": "http"}))
    with pytest.raises(NotImplementedError):
        adapter.invoke(
            request("aion.internal.noop", {}),
            runtime().model_copy(update={"runtime_type": "http"}),
        )


def request(capability_id: str, payload: dict[str, object]) -> CapabilityInvocationRequest:
    """Create an invocation request."""
    return CapabilityInvocationRequest(
        invocation_id="invocation-1",
        capability_id=capability_id,
        mode="controlled",
        payload=payload,
    )


def runtime() -> ModuleRuntime:
    """Create a runtime."""
    return ModuleRuntime(
        runtime_id="runtime-1",
        module_id="test.module",
        version="0.1.0",
        runtime_type="local_internal",
        endpoint_ref=None,
        status="active",
        health_status="healthy",
        config={},
    )
