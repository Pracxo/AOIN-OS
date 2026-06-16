"""MCP service tests."""

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.capabilities.registry import CapabilityRegistry
from aion_brain.capabilities.service import CapabilityService
from aion_brain.config import Settings
from aion_brain.contracts.mcp import (
    MCPInvocationRequest,
    MCPServerRecord,
    MCPServerRegistrationRequest,
    MCPSyncRequest,
)
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.mcp.repository import MCPRepository
from aion_brain.mcp.service import MCPPolicyDenied, MCPService
from tests.test_mcp_contracts import invocation_payload, server_payload


class FakePolicyAdapter:
    def __init__(self, *, allow: bool = True) -> None:
        self.allow = allow
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=self.allow,
            approval_required=False,
            reason="allowed" if self.allow else "denied",
            constraints=[] if self.allow else ["blocked"],
            audit_level="standard",
        )


class FakeTelemetry:
    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


def test_mcp_service_status_reports_disabled_by_default() -> None:
    service = make_service(enabled=False)

    status = service.status()

    assert status.enabled is False
    assert status.reason == "mcp_disabled"


def test_mcp_service_register_server_calls_policy_and_denies() -> None:
    policy = FakePolicyAdapter(allow=False)
    service = make_service(policy=policy)

    try:
        service.register_server(MCPServerRegistrationRequest(server=server(), activate=False))
    except MCPPolicyDenied:
        pass

    assert policy.requests[0].action_type == "mcp.server.register"


def test_mcp_service_sync_dry_run_discovers_fake_tools_without_persisting() -> None:
    service = make_service(enabled=True)
    service.register_server(MCPServerRegistrationRequest(server=server(), activate=True))

    response = service.sync_tools(
        MCPSyncRequest(
            mcp_server_id="mcp-server-1",
            dry_run=True,
            auto_register_capabilities=False,
            default_risk_level="medium",
            default_permissions_required=[],
            owner_scope=["workspace:main"],
            metadata={},
        )
    )

    assert response.status == "completed"
    assert response.discovered_tools == 3
    assert service.list_mappings() == []


def test_mcp_service_sync_auto_registers_capabilities_when_requested() -> None:
    registry = CapabilityRegistry()
    service = make_service(enabled=True, capability_service=CapabilityService(registry))
    service.register_server(MCPServerRegistrationRequest(server=server(), activate=True))

    response = service.sync_tools(
        MCPSyncRequest(
            mcp_server_id="mcp-server-1",
            dry_run=False,
            auto_register_capabilities=True,
            default_risk_level="low",
            default_permissions_required=[],
            owner_scope=["workspace:main"],
            metadata={},
        )
    )

    assert response.mapped_capabilities == 3
    assert len(service.list_mappings(status="active")) == 3
    assert registry.capability_exists("mcp.test-server.echo")


def test_mcp_service_invoke_dry_run_and_controlled_modes() -> None:
    disabled = make_service(enabled=False)
    enabled = make_service(enabled=True)
    for service in (disabled, enabled):
        service.register_server(MCPServerRegistrationRequest(server=server(), activate=True))
        service.sync_tools(
            MCPSyncRequest(
                mcp_server_id="mcp-server-1",
                dry_run=False,
                auto_register_capabilities=True,
                default_risk_level="low",
                default_permissions_required=[],
                owner_scope=["workspace:main"],
                metadata={},
            )
        )

    generated_payload = {**invocation_payload(), "capability_id": "mcp.test-server.echo"}
    dry_run = disabled.invoke(MCPInvocationRequest(**generated_payload))
    disabled_controlled = disabled.invoke(
        MCPInvocationRequest(**{**generated_payload, "mode": "controlled"})
    )
    completed = enabled.invoke(
        MCPInvocationRequest(**{**generated_payload, "mode": "controlled", "payload": {"value": 1}})
    )
    missing = enabled.invoke(
        MCPInvocationRequest(**{**generated_payload, "capability_id": "missing"})
    )

    assert dry_run.status == "dry_run"
    assert disabled_controlled.status == "mcp_disabled"
    assert completed.status == "completed"
    assert completed.output == {"echo": {"value": 1}}
    assert missing.status == "tool_not_found"


def test_mcp_service_emits_visual_telemetry() -> None:
    telemetry = FakeTelemetry()
    service = make_service(enabled=True, telemetry=telemetry)
    service.register_server(MCPServerRegistrationRequest(server=server(), activate=True))
    service.sync_tools(
        MCPSyncRequest(
            mcp_server_id="mcp-server-1",
            dry_run=True,
            owner_scope=["workspace:main"],
        )
    )
    service.invoke(MCPInvocationRequest(**invocation_payload()))

    event_types = [getattr(event, "event_type", None) for event in telemetry.events]
    assert "mcp_server_registered" in event_types
    assert "mcp_tools_synced" in event_types
    assert "mcp_tool_invocation_started" in event_types
    assert "mcp_tool_invocation_recorded" in event_types


def make_service(
    *,
    enabled: bool = True,
    policy: FakePolicyAdapter | None = None,
    telemetry: FakeTelemetry | None = None,
    capability_service: CapabilityService | None = None,
) -> MCPService:
    return MCPService(
        mcp_repository=MCPRepository(engine=sqlite_engine()),
        capability_service=capability_service or CapabilityService(CapabilityRegistry()),
        policy_adapter=policy or FakePolicyAdapter(),
        telemetry_service=telemetry,
        settings=Settings(_env_file=None, AION_MCP_ENABLED=enabled),
    )


def server() -> MCPServerRecord:
    return MCPServerRecord(**server_payload())


def sqlite_engine():
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
