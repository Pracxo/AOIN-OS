"""Policy-gated MCP service behind AION contracts."""

from datetime import UTC, datetime
from time import perf_counter
from typing import Any, cast
from uuid import uuid4

from aion_brain.approvals.integration import evaluate_approval_gate
from aion_brain.capabilities.service import CapabilityService
from aion_brain.config import Settings
from aion_brain.contracts.autonomy import AutonomyDecisionRequest
from aion_brain.contracts.mcp import (
    MCPAdapterStatus,
    MCPCapabilityMapping,
    MCPInvocationRequest,
    MCPInvocationResult,
    MCPRiskLevel,
    MCPServerHealth,
    MCPServerRecord,
    MCPServerRegistrationRequest,
    MCPSyncRequest,
    MCPSyncResponse,
    MCPToolDescriptor,
)
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.sandbox import SandboxRunRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.mcp.compat import MCPCompat
from aion_brain.mcp.in_memory_fake_server import InMemoryFakeMCPServer
from aion_brain.mcp.repository import MCPRepository
from aion_brain.mcp.schema_mapper import (
    mapping_to_capability_manifest,
    tool_to_capability_mapping,
)
from aion_brain.mcp.security import validate_mcp_server_security
from aion_brain.policy.base import PolicyAdapter


class MCPPolicyDenied(Exception):
    """Raised when policy denies an MCP action."""

    def __init__(self, decision: PolicyDecision) -> None:
        super().__init__(decision.reason)
        self.decision = decision


class MCPService:
    """Govern optional MCP discovery and invocation through AION contracts."""

    def __init__(
        self,
        *,
        mcp_repository: MCPRepository,
        capability_service: CapabilityService | object | None,
        policy_adapter: PolicyAdapter,
        telemetry_service: object | None,
        settings: Settings,
        compat: MCPCompat | None = None,
        fake_server: InMemoryFakeMCPServer | None = None,
        approval_service: object | None = None,
        autonomy_governor: object | None = None,
        sandbox_service: object | None = None,
    ) -> None:
        self._repository = mcp_repository
        self._capability_service = capability_service
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._settings = settings
        self._compat = compat or MCPCompat()
        self._fake_server = fake_server or InMemoryFakeMCPServer()
        self._approval_service = approval_service
        self._autonomy_governor = autonomy_governor
        self._sandbox_service = sandbox_service

    def status(self) -> MCPAdapterStatus:
        """Return process-local MCP adapter status."""
        available = self._compat.is_available()
        reason = (
            "mcp_disabled"
            if not self._settings.mcp_enabled
            else None
            if available
            else self._compat.availability_reason()
        )
        return MCPAdapterStatus(
            adapter_name="mcp",
            enabled=self._settings.mcp_enabled,
            package_available=available,
            network_allowed=self._settings.mcp_allow_network,
            stdio_allowed=self._settings.mcp_allow_stdio,
            reason=reason,
            metadata={"timeout_seconds": self._settings.mcp_timeout_seconds},
        )

    def register_server(self, request: MCPServerRegistrationRequest) -> MCPServerRecord:
        """Register an MCP server boundary."""
        decision = self._authorize(
            action_type="mcp.server.register",
            resource_type="mcp_server",
            resource_id=request.server.mcp_server_id,
            risk_level="medium",
            scope=request.server.owner_scope,
            approval_present=True,
            context={"server_name": request.server.server_name},
        )
        if not decision.allow:
            raise MCPPolicyDenied(decision)
        reasons = validate_mcp_server_security(request.server, self._settings)
        status = "active" if request.activate and not reasons else request.server.status
        saved = self._repository.create_server(
            request.server.model_copy(
                update={
                    "status": status,
                    "health_status": request.server.health_status or "unknown",
                    "updated_at": datetime.now(UTC),
                }
            )
        )
        self._emit(
            "mcp_server_registered",
            "server",
            saved.mcp_server_id,
            0.5,
            {"status": saved.status},
        )
        if reasons:
            self._emit_security_blocked(saved, reasons)
        if request.discover_tools:
            self.sync_tools(
                MCPSyncRequest(
                    mcp_server_id=saved.mcp_server_id,
                    dry_run=not self._settings.mcp_auto_register_capabilities,
                    auto_register_capabilities=self._settings.mcp_auto_register_capabilities,
                    default_risk_level=cast(MCPRiskLevel, self._settings.mcp_default_risk_level),
                    default_permissions_required=[],
                    owner_scope=saved.owner_scope,
                    metadata={"registration": True},
                )
            )
        return saved

    def get_server(self, mcp_server_id: str) -> MCPServerRecord | None:
        """Return one registered MCP server."""
        return self._repository.get_server(mcp_server_id)

    def list_servers(self, status: str | None = None) -> list[MCPServerRecord]:
        """List registered MCP servers."""
        return self._repository.list_servers(status)

    def disable_server(
        self,
        mcp_server_id: str,
        reason: str | None = None,
    ) -> MCPServerRecord:
        """Disable one MCP server."""
        decision = self._authorize(
            action_type="mcp.server.disable",
            resource_type="mcp_server",
            resource_id=mcp_server_id,
            risk_level="medium",
            scope=["workspace:main"],
            approval_present=True,
            context={"reason": reason},
        )
        if not decision.allow:
            raise MCPPolicyDenied(decision)
        return self._repository.disable_server(mcp_server_id, reason)

    def health_check(self, mcp_server_id: str) -> MCPServerHealth:
        """Run a non-executing MCP server health check."""
        server = self._repository.get_server(mcp_server_id)
        if server is None:
            return _health(mcp_server_id, "unavailable", {"reason": "server_not_found"})
        decision = self._authorize(
            action_type="mcp.server.health_check",
            resource_type="mcp_server",
            resource_id=mcp_server_id,
            risk_level="low",
            scope=server.owner_scope,
            approval_present=False,
            context={"transport_type": server.transport_type},
        )
        if not decision.allow:
            return _health(mcp_server_id, "unhealthy", {"reason": decision.reason})
        if not self._settings.mcp_enabled:
            health = _health(mcp_server_id, "unavailable", {"reason": "mcp_disabled"})
        elif server.transport_type == "in_memory_fake":
            health = _health(mcp_server_id, "healthy", {"transport_type": "in_memory_fake"})
        elif not self._compat.is_available():
            health = _health(mcp_server_id, "unavailable", {"reason": "package_unavailable"})
        else:
            reasons = validate_mcp_server_security(server, self._settings)
            health = (
                _health(mcp_server_id, "unhealthy", {"reasons": reasons})
                if reasons
                else _health(mcp_server_id, "degraded", {"reason": "real_health_not_executed"})
            )
        self._repository.update_server_health(mcp_server_id, health)
        intensity = {"healthy": 0.8, "degraded": 0.4, "unhealthy": 0.2, "unavailable": 0.2}
        self._emit(
            "mcp_server_health_checked",
            "server",
            mcp_server_id,
            intensity[health.status],
            {"status": health.status, **health.details},
        )
        return health

    def sync_tools(self, request: MCPSyncRequest) -> MCPSyncResponse:
        """Discover tools and optionally persist AION capability mappings."""
        decision = self._authorize(
            action_type="mcp.tools.sync",
            resource_type="mcp_server",
            resource_id=request.mcp_server_id,
            risk_level="medium",
            scope=request.owner_scope,
            approval_present=True,
            context={"dry_run": request.dry_run},
        )
        if not decision.allow:
            response = _sync_response(request, [], "blocked_by_policy", decision.reason, [])
            return self._repository.record_sync(response)
        server = self._repository.get_server(request.mcp_server_id)
        if server is None:
            response = _sync_response(
                request,
                [],
                "server_unavailable",
                "server_not_found",
                [{"reason": "server_not_found"}],
            )
            return self._repository.record_sync(response)
        if not self._settings.mcp_enabled and server.transport_type != "in_memory_fake":
            response = _sync_response(request, [], "mcp_disabled", "mcp_disabled", [])
            self._emit("mcp_disabled", "mcp", "mcp", 0.4, {"operation": "sync"})
            return self._repository.record_sync(response)
        reasons = validate_mcp_server_security(server, self._settings)
        if server.transport_type == "in_memory_fake":
            reasons = [reason for reason in reasons if reason != "mcp_disabled"]
        if reasons:
            self._emit_security_blocked(server, reasons)
            response = _sync_response(
                request,
                [],
                "server_unavailable",
                "security_blocked",
                [{"reason": reason} for reason in reasons],
            )
            return self._repository.record_sync(response)
        try:
            tools = self._discover_tools(server)
            mappings = [
                tool_to_capability_mapping(
                    server,
                    tool,
                    {
                        "risk_level": request.default_risk_level,
                        "permissions_required": request.default_permissions_required,
                    },
                )
                for tool in tools
            ]
        except Exception as exc:
            response = _sync_response(
                request,
                [],
                "failed",
                "tool_discovery_failed",
                [{"reason": str(exc)}],
            )
            return self._repository.record_sync(response)
        if not request.dry_run and request.auto_register_capabilities:
            for mapping in mappings:
                self._repository.upsert_mapping(mapping)
            self._register_manifest(server, mappings)
        response = _sync_response(request, mappings, "completed", None, [])
        self._repository.record_sync(response)
        self._emit(
            "mcp_tools_synced",
            "mcp",
            response.sync_id,
            0.6,
            {
                "discovered_tools": response.discovered_tools,
                "mapped_capabilities": response.mapped_capabilities,
                "dry_run": request.dry_run,
            },
        )
        return response

    def list_mappings(
        self,
        mcp_server_id: str | None = None,
        status: str | None = None,
    ) -> list[MCPCapabilityMapping]:
        """List MCP capability mappings."""
        return self._repository.list_mappings(mcp_server_id, status)

    def get_mapping_by_capability(self, capability_id: str) -> MCPCapabilityMapping | None:
        """Return an MCP mapping by AION capability ID."""
        return self._repository.get_mapping_by_capability(capability_id)

    def invoke(self, request: MCPInvocationRequest) -> MCPInvocationResult:
        """Invoke or dry-run an MCP-backed capability."""
        started = perf_counter()
        self._emit(
            "mcp_tool_invocation_started",
            "tool",
            request.mcp_tool_name,
            0.6,
            {"mode": request.mode, "capability_id": request.capability_id},
        )
        mapping = self._mapping_for_request(request)
        if mapping is None:
            return self._record_invocation(
                request,
                "tool_not_found",
                {},
                {"reason": "mapping_not_found"},
                None,
                started,
            )
        decision = self._authorize(
            action_type="mcp.tool.invoke",
            resource_type="mcp_tool",
            resource_id=request.capability_id,
            risk_level=mapping.risk_level,
            scope=mapping.memory_read_scopes or ["workspace:main"],
            approval_present=request.approval_present,
            context={
                "mode": request.mode,
                "mcp_enabled": self._settings.mcp_enabled,
                "transport_type": request.metadata.get("transport_type"),
            },
        )
        if not decision.allow:
            return self._record_invocation(
                request,
                "blocked_by_policy",
                {},
                {"reason": decision.reason, "constraints": decision.constraints},
                decision.decision_id,
                started,
            )
        autonomy = self._autonomy_decision(request, mapping.risk_level)
        if autonomy is not None and not bool(getattr(autonomy, "allow", False)):
            return self._record_invocation(
                request,
                "blocked_by_policy",
                {},
                {
                    "reason": str(getattr(autonomy, "reason", "autonomy_denied")),
                    "autonomy_decision_id": getattr(autonomy, "autonomy_decision_id", None),
                },
                decision.decision_id,
                started,
            )
        sandbox_error = self._sandbox_boundary_error(request)
        if sandbox_error is not None:
            return self._record_invocation(
                request,
                "blocked_by_policy",
                {},
                sandbox_error,
                decision.decision_id,
                started,
            )
        if request.mode == "dry_run":
            return self._record_invocation(
                request,
                "dry_run",
                {
                    "dry_run": True,
                    "capability_id": request.capability_id,
                    "mcp_tool_name": request.mcp_tool_name,
                },
                {},
                decision.decision_id,
                started,
            )
        if not self._settings.mcp_enabled:
            self._emit("mcp_disabled", "mcp", "mcp", 0.4, {"operation": "invoke"})
            return self._record_invocation(
                request,
                "mcp_disabled",
                {},
                {"reason": "mcp_disabled"},
                decision.decision_id,
                started,
            )
        if request.mode == "controlled" and not request.approval_present:
            gate = evaluate_approval_gate(
                self._approval_service,
                trace_id=request.trace_id,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                action_type="mcp.tool.invoke",
                resource_type="mcp_tool",
                resource_id=request.capability_id,
                requested_risk_level=mapping.risk_level,
                security_scope=mapping.memory_read_scopes or ["workspace:main"],
                payload={"capability_id": request.capability_id, "tool": request.mcp_tool_name},
                context={
                    "mode": request.mode,
                    "approval_present": request.approval_present,
                    "uses_mcp": True,
                    "external_effect_possible": True,
                    "controlled_execution": True,
                },
                metadata=request.metadata,
            )
            if gate is not None and gate.final_decision != "allow":
                return self._record_invocation(
                    request,
                    "blocked_by_policy",
                    {},
                    {
                        "reason": (
                            gate.reason if gate.final_decision == "block" else "approval_required"
                        ),
                        "approval_request_id": gate.approval_request_id,
                    },
                    decision.decision_id,
                    started,
                )
        if mapping.risk_level in {"high", "critical"} and not request.approval_present:
            return self._record_invocation(
                request,
                "blocked_by_policy",
                {},
                {"reason": "approval_required"},
                decision.decision_id,
                started,
            )
        server = self._repository.get_server(request.mcp_server_id)
        if server is None or server.status == "disabled":
            return self._record_invocation(
                request,
                "server_unavailable",
                {},
                {"reason": "server_unavailable"},
                decision.decision_id,
                started,
            )
        reasons = validate_mcp_server_security(server, self._settings)
        if reasons:
            self._emit_security_blocked(server, reasons)
            return self._record_invocation(
                request,
                "server_unavailable",
                {},
                {"reasons": reasons},
                decision.decision_id,
                started,
            )
        try:
            output = self._call_tool(server, request.mcp_tool_name, request.payload)
            return self._record_invocation(
                request,
                "completed",
                output,
                {},
                decision.decision_id,
                started,
            )
        except KeyError:
            return self._record_invocation(
                request,
                "tool_not_found",
                {},
                {"reason": "tool_not_found"},
                decision.decision_id,
                started,
            )
        except Exception as exc:
            return self._record_invocation(
                request,
                "failed",
                {},
                {"reason": str(exc)},
                decision.decision_id,
                started,
            )

    def _sandbox_boundary_error(self, request: MCPInvocationRequest) -> dict[str, Any] | None:
        sandbox_profile_id = request.metadata.get("sandbox_profile_id")
        if sandbox_profile_id is None:
            return None
        if self._sandbox_service is None:
            return {"reason": "sandbox_service_unavailable"}
        profile_id = str(sandbox_profile_id)
        has_grant = getattr(self._sandbox_service, "has_active_grant", None)
        if callable(has_grant) and not bool(
            has_grant(
                target_type="mcp_server",
                target_id=request.mcp_server_id,
                sandbox_profile_id=profile_id,
            )
        ):
            return {"reason": "runtime_permission_grant_required"}
        run = getattr(self._sandbox_service, "run", None)
        if not callable(run):
            return {"reason": "sandbox_service_unavailable"}
        result = run(
            SandboxRunRequest(
                trace_id=request.trace_id,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                sandbox_profile_id=profile_id,
                target_type="mcp_tool",
                target_id=request.capability_id,
                mode=request.mode,
                input={"mcp_tool_name": request.mcp_tool_name},
                approval_present=request.approval_present,
                metadata={"source": "mcp_service"},
            )
        )
        status = str(getattr(result, "status", "failed"))
        if status not in {"dry_run", "completed"}:
            return {
                "reason": "sandbox_validation_failed",
                "sandbox_run_id": getattr(result, "sandbox_run_id", None),
                "sandbox_status": status,
            }
        return None

    def _discover_tools(self, server: MCPServerRecord) -> list[MCPToolDescriptor]:
        if server.transport_type == "in_memory_fake":
            return self._fake_server.list_tools()
        client = self._compat.create_client(server)
        try:
            return self._compat.list_tools(client, server)
        finally:
            self._compat.close(client)

    def _call_tool(
        self,
        server: MCPServerRecord,
        tool_name: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        if server.transport_type == "in_memory_fake":
            return self._fake_server.call_tool(tool_name, payload)
        client = self._compat.create_client(server)
        try:
            return self._compat.call_tool(client, server, tool_name, payload)
        finally:
            self._compat.close(client)

    def _mapping_for_request(
        self,
        request: MCPInvocationRequest,
    ) -> MCPCapabilityMapping | None:
        mapping = self._repository.get_mapping_by_capability(request.capability_id)
        if mapping is not None:
            return mapping
        tool_mapping = self._repository.get_mapping_by_tool(
            request.mcp_server_id,
            request.mcp_tool_name,
        )
        if tool_mapping is not None and tool_mapping.capability_id == request.capability_id:
            return tool_mapping
        return None

    def _register_manifest(
        self,
        server: MCPServerRecord,
        mappings: list[MCPCapabilityMapping],
    ) -> None:
        register_manifest = getattr(self._capability_service, "register_manifest", None)
        if callable(register_manifest):
            register_manifest(mapping_to_capability_manifest(server, mappings))

    def _record_invocation(
        self,
        request: MCPInvocationRequest,
        status: str,
        output: dict[str, Any],
        error: dict[str, Any],
        policy_decision_id: str | None,
        started: float,
    ) -> MCPInvocationResult:
        mcp_invocation_id = request.mcp_invocation_id or f"mcp-invocation-{uuid4().hex}"
        result = MCPInvocationResult(
            mcp_invocation_id=mcp_invocation_id,
            invocation_id=request.invocation_id,
            mcp_server_id=request.mcp_server_id,
            mcp_tool_name=request.mcp_tool_name,
            capability_id=request.capability_id,
            status=status,  # type: ignore[arg-type]
            output=output,
            error=error,
            latency_ms=max(0, int((perf_counter() - started) * 1000)),
            policy_decision_id=policy_decision_id,
            created_at=datetime.now(UTC),
        )
        self._repository.record_invocation(result)
        intensity = 1.0 if status == "completed" else 0.5 if status == "dry_run" else 0.9
        self._emit(
            "mcp_tool_invocation_recorded",
            "tool",
            mcp_invocation_id,
            intensity,
            {"status": status, "capability_id": request.capability_id},
        )
        return result

    def _autonomy_decision(self, request: MCPInvocationRequest, risk_level: str) -> object | None:
        decide = getattr(self._autonomy_governor, "decide", None)
        if not callable(decide):
            return None
        requested_mode = "dry_run" if request.mode == "dry_run" else "supervised_controlled"
        return cast(
            object,
            decide(
                AutonomyDecisionRequest(
                    trace_id=request.trace_id,
                    actor_id=request.actor_id,
                    workspace_id=request.workspace_id,
                    requested_mode=cast(Any, requested_mode),
                    action_type="mcp.tool.invoke",
                    resource_type="mcp_tool",
                    resource_id=request.capability_id,
                    risk_level=cast(Any, risk_level),
                    approval_present=request.approval_present,
                    delegation_id=_metadata_str(request.metadata, "delegation_id"),
                    context={
                        "mode": request.mode,
                        "security_scope": request.metadata.get(
                            "security_scope",
                            ["workspace:main"],
                        ),
                        "uses_external_tool": request.mode == "controlled",
                    },
                    metadata=request.metadata,
                )
            ),
        )

    def _authorize(
        self,
        *,
        action_type: str,
        resource_type: str,
        resource_id: str | None,
        risk_level: str,
        scope: list[str],
        approval_present: bool,
        context: dict[str, Any],
    ) -> PolicyDecision:
        return self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{resource_id or 'mcp'}",
                trace_id=None,
                actor_id=None,
                workspace_id=None,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                risk_level=risk_level,
                approval_present=approval_present,
                requested_permissions=[],
                security_scope=scope,
                context=context,
            )
        )

    def _emit_security_blocked(self, server: MCPServerRecord, reasons: list[str]) -> None:
        self._emit(
            "mcp_security_blocked",
            "mcp",
            server.mcp_server_id,
            0.9,
            {"reasons": reasons, "transport_type": server.transport_type},
        )

    def _emit(
        self,
        event_type: str,
        node_type: str,
        node_id: str,
        intensity: float,
        payload: dict[str, Any],
    ) -> None:
        if self._telemetry_service is None:
            return
        trace_id = payload.get("trace_id")
        event = VisualTelemetryEvent(
            telemetry_id=f"telemetry-mcp-{event_type}-{node_id}",
            trace_id=trace_id if isinstance(trace_id, str) else node_id,
            event_type=event_type,  # type: ignore[arg-type]
            node_type=node_type,  # type: ignore[arg-type]
            node_id=node_id,
            edge_from=None,
            edge_to=None,
            intensity=max(0.0, min(1.0, intensity)),
            payload=payload,
            created_at=datetime.now(UTC),
        )
        try:
            emit = getattr(self._telemetry_service, "emit", None)
            if callable(emit):
                emit(event)
                return
            save = getattr(self._telemetry_service, "save_visual_telemetry", None)
            if callable(save):
                save(event.trace_id, [event])
        except Exception:
            return


def _health(
    mcp_server_id: str,
    status: str,
    details: dict[str, Any],
) -> MCPServerHealth:
    return MCPServerHealth(
        mcp_server_id=mcp_server_id,
        status=status,  # type: ignore[arg-type]
        latency_ms=0,
        details=details,
        checked_at=datetime.now(UTC),
    )


def _sync_response(
    request: MCPSyncRequest,
    mappings: list[MCPCapabilityMapping],
    status: str,
    reason: str | None,
    errors: list[dict[str, Any]],
) -> MCPSyncResponse:
    failed = len(errors)
    return MCPSyncResponse(
        sync_id=f"mcp-sync-{uuid4().hex}",
        mcp_server_id=request.mcp_server_id,
        dry_run=request.dry_run,
        discovered_tools=len(mappings),
        mapped_capabilities=len(mappings) if status == "completed" else 0,
        skipped=0,
        failed=failed,
        mappings=mappings,
        errors=errors,
        status=status,  # type: ignore[arg-type]
        reason=reason,
        created_at=datetime.now(UTC),
    )


def _metadata_str(metadata: dict[str, Any], key: str) -> str | None:
    value = metadata.get(key)
    return value if isinstance(value, str) and value else None
