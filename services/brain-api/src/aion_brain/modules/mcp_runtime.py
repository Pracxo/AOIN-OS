"""MCP module runtime adapter."""

from datetime import UTC, datetime
from typing import Any, cast

from aion_brain.contracts.mcp import MCPInvocationRequest, MCPInvocationResult
from aion_brain.contracts.modules import (
    CapabilityInvocationRequest,
    CapabilityInvocationResult,
    ModuleHealthCheck,
    ModuleRuntime,
)


class MCPRuntimeAdapter:
    """MCP runtime adapter that exposes only AION contracts."""

    def __init__(self, mcp_service: object | None = None) -> None:
        self._mcp_service = mcp_service

    def health_check(self, runtime: ModuleRuntime) -> ModuleHealthCheck:
        """Return MCP runtime health through AION contracts."""
        server_id = _server_id(runtime)
        if self._mcp_service is None or server_id is None:
            return _health(runtime, "degraded", {"reason": "mcp_service_not_configured"})
        health_check = getattr(self._mcp_service, "health_check", None)
        if not callable(health_check):
            return _health(runtime, "degraded", {"reason": "mcp_health_unavailable"})
        health = health_check(server_id)
        status = "healthy" if getattr(health, "status", None) == "healthy" else "degraded"
        return _health(
            runtime,
            status,
            {
                "mcp_server_id": server_id,
                "mcp_status": getattr(health, "status", "unavailable"),
                **dict(getattr(health, "details", {}) or {}),
            },
        )

    def invoke(
        self,
        request: CapabilityInvocationRequest,
        runtime: ModuleRuntime,
    ) -> CapabilityInvocationResult:
        """Invoke MCP through MCPService without exposing MCP objects."""
        if self._mcp_service is None:
            return _result(
                request,
                runtime,
                "not_implemented",
                {},
                {"reason": "mcp_service_not_configured"},
                None,
            )
        mapping = _mapping(self._mcp_service, request, runtime)
        if mapping is None:
            return _result(
                request,
                runtime,
                "capability_not_found",
                {},
                {"reason": "mcp_mapping_not_found"},
                None,
            )
        invoke = getattr(self._mcp_service, "invoke", None)
        if not callable(invoke):
            return _result(
                request,
                runtime,
                "not_implemented",
                {},
                {"reason": "mcp_invoke_unavailable"},
                None,
            )
        mcp_result = cast(
            MCPInvocationResult,
            invoke(
                MCPInvocationRequest(
                    mcp_invocation_id=None,
                    invocation_id=request.invocation_id,
                    mcp_server_id=mapping.mcp_server_id,
                    mcp_tool_name=mapping.mcp_tool_name,
                    capability_id=request.capability_id,
                    trace_id=request.trace_id,
                    execution_id=request.execution_id,
                    step_run_id=request.step_run_id,
                    actor_id=request.actor_id,
                    workspace_id=request.workspace_id,
                    mode=request.mode,
                    payload=request.payload,
                    approval_present=request.approval_present,
                    metadata={
                        **request.metadata,
                        "runtime_id": runtime.runtime_id,
                        "transport_type": runtime.config.get("transport_type"),
                    },
                )
            ),
        )
        return _result(
            request,
            runtime,
            _capability_status(mcp_result.status),
            mcp_result.output,
            mcp_result.error,
            mcp_result.policy_decision_id,
        )


def _mapping(service: object, request: CapabilityInvocationRequest, runtime: ModuleRuntime) -> Any:
    get_mapping = getattr(service, "get_mapping_by_capability", None)
    if callable(get_mapping):
        mapping = get_mapping(request.capability_id)
        if mapping is not None:
            return mapping
    mcp_server_id = request.metadata.get("mcp_server_id") or runtime.config.get("mcp_server_id")
    mcp_tool_name = request.metadata.get("mcp_tool_name") or runtime.config.get("mcp_tool_name")
    if isinstance(mcp_server_id, str) and isinstance(mcp_tool_name, str):
        return _AdhocMapping(mcp_server_id, mcp_tool_name)
    return None


class _AdhocMapping:
    def __init__(self, mcp_server_id: str, mcp_tool_name: str) -> None:
        self.mcp_server_id = mcp_server_id
        self.mcp_tool_name = mcp_tool_name


def _server_id(runtime: ModuleRuntime) -> str | None:
    value = runtime.config.get("mcp_server_id")
    return value if isinstance(value, str) else None


def _health(
    runtime: ModuleRuntime,
    status: str,
    details: dict[str, Any],
) -> ModuleHealthCheck:
    return ModuleHealthCheck(
        health_check_id=f"health-{runtime.runtime_id}-{datetime.now(UTC).timestamp()}",
        runtime_id=runtime.runtime_id,
        module_id=runtime.module_id,
        status=cast(Any, status),
        latency_ms=0,
        details=details,
        created_at=datetime.now(UTC),
    )


def _result(
    request: CapabilityInvocationRequest,
    runtime: ModuleRuntime,
    status: str,
    output: dict[str, Any],
    error: dict[str, Any],
    policy_decision_id: str | None,
) -> CapabilityInvocationResult:
    return CapabilityInvocationResult(
        invocation_id=request.invocation_id,
        capability_id=request.capability_id,
        runtime_id=runtime.runtime_id,
        status=cast(Any, status),
        output=output,
        error=error,
        policy_decision_id=policy_decision_id,
        latency_ms=0,
        created_at=datetime.now(UTC),
    )


def _capability_status(status: str) -> str:
    if status in {"dry_run", "completed", "blocked_by_policy", "failed", "not_implemented"}:
        return status
    if status == "tool_not_found":
        return "capability_not_found"
    if status in {"mcp_disabled", "server_unavailable"}:
        return "runtime_unhealthy"
    return "failed"
