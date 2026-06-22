"""Runtime gateway MCP tests."""

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.capabilities.registry import CapabilityRegistry
from aion_brain.contracts.capabilities import CapabilityManifest
from aion_brain.contracts.modules import (
    CapabilityInvocationRequest,
    CapabilityRuntimeBinding,
    ModuleRuntime,
)
from aion_brain.modules.mcp_runtime import MCPRuntimeAdapter
from aion_brain.modules.repository import ModuleRuntimeRepository
from aion_brain.modules.runtime_gateway import CapabilityRuntimeGateway
from tests.test_mcp_contracts import mapping_payload
from tests.test_mcp_service import FakePolicyAdapter, make_service, server


def test_runtime_gateway_supports_mcp_runtime_disabled_by_default() -> None:
    service = make_service(enabled=False)
    service._repository.create_server(server())  # noqa: SLF001
    service._repository.upsert_mapping(mapping())  # noqa: SLF001
    repository = ModuleRuntimeRepository(engine=sqlite_engine())
    repository.save_runtime(runtime())
    repository.save_binding(binding())
    registry = CapabilityRegistry()
    registry.register(
        CapabilityManifest(
            module_id="mcp.test",
            version="0.1.0",
            capabilities=[{"capability_id": "mcp.test.echo"}],
            permissions_required=[],
            memory_read_scopes=[],
            memory_write_scopes=[],
            events_subscribed=[],
            events_published=[],
            execution_mode="sync",
        )
    )
    gateway = CapabilityRuntimeGateway(
        module_runtime_repository=repository,
        capability_registry=registry,
        policy_adapter=FakePolicyAdapter(),
        runtime_adapters={"mcp": MCPRuntimeAdapter(service)},
    )

    dry_run = gateway.invoke(
        CapabilityInvocationRequest(
            invocation_id="invocation-1",
            capability_id="mcp.test.echo",
            mode="dry_run",
            payload={},
        )
    )
    controlled = gateway.invoke(
        CapabilityInvocationRequest(
            invocation_id="invocation-2",
            capability_id="mcp.test.echo",
            mode="controlled",
            payload={},
        )
    )

    assert dry_run.status == "dry_run"
    assert controlled.status == "runtime_unhealthy"


def runtime() -> ModuleRuntime:
    return ModuleRuntime(
        runtime_id="runtime-mcp-1",
        module_id="mcp.test",
        version="0.1.0",
        runtime_type="mcp",
        endpoint_ref=None,
        status="active",
        health_status="healthy",
        config={"mcp_server_id": "mcp-server-1", "transport_type": "in_memory_fake"},
    )


def binding() -> CapabilityRuntimeBinding:
    return CapabilityRuntimeBinding(
        binding_id="binding-mcp-test-echo-runtime-mcp-1-controlled",
        capability_id="mcp.test.echo",
        module_id="mcp.test",
        runtime_id="runtime-mcp-1",
        invocation_mode="controlled",
        status="active",
    )


def mapping():
    from aion_brain.contracts.mcp import MCPCapabilityMapping

    return MCPCapabilityMapping(**mapping_payload())


def sqlite_engine():
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
