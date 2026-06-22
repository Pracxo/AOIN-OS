"""Local internal runtime tests."""

import inspect

from aion_brain.contracts.modules import CapabilityInvocationRequest, ModuleRuntime
from aion_brain.modules import local_internal_runtime
from aion_brain.modules.local_internal_runtime import LocalInternalRuntimeAdapter


def test_local_internal_runtime_executes_noop() -> None:
    """Local internal runtime executes generic noop deterministically."""
    result = LocalInternalRuntimeAdapter().invoke(
        request("aion.internal.noop", {}),
        runtime(),
    )

    assert result.status == "completed"
    assert result.output["message"] == "No operation performed."


def test_local_internal_runtime_executes_echo() -> None:
    """Local internal runtime echoes payload without external side effects."""
    payload = {"message": "hello"}
    result = LocalInternalRuntimeAdapter().invoke(
        request("aion.internal.echo", payload),
        runtime(),
    )

    assert result.status == "completed"
    assert result.output["echo"] == payload


def test_local_internal_runtime_avoids_external_call_imports() -> None:
    """The safe runtime does not import obvious external execution tools."""
    source = inspect.getsource(local_internal_runtime)

    assert "subprocess" not in source
    assert "httpx" not in source
    assert "requests" not in source
    assert "selenium" not in source


def request(capability_id: str, payload: dict[str, object]) -> CapabilityInvocationRequest:
    """Create an invocation request."""
    return CapabilityInvocationRequest(
        invocation_id="invocation-1",
        capability_id=capability_id,
        mode="controlled",
        payload=payload,
    )


def runtime() -> ModuleRuntime:
    """Create a local internal runtime."""
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
