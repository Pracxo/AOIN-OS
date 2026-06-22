"""MCP runtime adapter tests."""

from aion_brain.contracts.modules import CapabilityInvocationRequest, ModuleRuntime
from aion_brain.modules.mcp_runtime import MCPRuntimeAdapter
from tests.test_mcp_contracts import mapping_payload
from tests.test_mcp_service import make_service, server


def test_mcp_runtime_adapter_maps_capability_invocation_to_mcp_request() -> None:
    service = make_service(enabled=True)
    service._repository.create_server(server())  # noqa: SLF001
    service._repository.upsert_mapping(mapping())  # noqa: SLF001
    adapter = MCPRuntimeAdapter(service)

    result = adapter.invoke(
        CapabilityInvocationRequest(
            invocation_id="invocation-1",
            capability_id="mcp.test.echo",
            mode="controlled",
            payload={"value": 1},
        ),
        ModuleRuntime(
            runtime_id="runtime-mcp-1",
            module_id="mcp.test",
            version="0.1.0",
            runtime_type="mcp",
            endpoint_ref=None,
            status="active",
            health_status="healthy",
            config={"mcp_server_id": "mcp-server-1", "transport_type": "in_memory_fake"},
        ),
    )

    assert result.status == "completed"
    assert result.output == {"echo": {"value": 1}}


def mapping():
    from aion_brain.contracts.mcp import MCPCapabilityMapping

    return MCPCapabilityMapping(**mapping_payload())
