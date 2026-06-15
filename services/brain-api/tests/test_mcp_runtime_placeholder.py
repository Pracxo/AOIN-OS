"""MCP runtime adapter guard tests."""

import ast
import inspect

from aion_brain.contracts.modules import CapabilityInvocationRequest, ModuleRuntime
from aion_brain.modules import mcp_runtime
from aion_brain.modules.mcp_runtime import MCPRuntimeAdapter


def test_mcp_runtime_adapter_is_guarded_without_service() -> None:
    """MCP runtime returns AION statuses without importing MCP SDKs directly."""
    adapter = MCPRuntimeAdapter()

    health = adapter.health_check(runtime().model_copy(update={"runtime_type": "mcp"}))
    result = adapter.invoke(
        request("aion.internal.noop", {}),
        runtime().model_copy(update={"runtime_type": "mcp"}),
    )

    assert health.status == "degraded"
    assert health.details["reason"] == "mcp_service_not_configured"
    assert result.status == "not_implemented"
    assert result.error["reason"] == "mcp_service_not_configured"
    source = inspect.getsource(mcp_runtime)
    imports = [
        imported
        for node in ast.walk(ast.parse(source))
        for imported in _imported_modules(node)
    ]
    assert "mcp" not in imports
    assert all(not imported.startswith("mcp.") for imported in imports)


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


def _imported_modules(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if isinstance(node, ast.ImportFrom) and node.module is not None:
        return [node.module]
    return []
