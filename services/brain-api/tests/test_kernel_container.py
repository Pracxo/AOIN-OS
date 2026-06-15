"""Kernel container tests."""


from aion_brain.config import Settings
from aion_brain.kernel.container import KernelContainer
from tests.kernel_fakes import kernel_container


def test_container_constructs_required_services() -> None:
    container = kernel_container()
    assert container.reasoning_mesh is not None
    assert container.execution_orchestrator is not None
    assert container.retrieval_router is not None
    assert container.policy_catalog_service is not None
    assert container.permission_matrix_service is not None
    assert len(container.service_registry.list_services()) >= 10


def test_container_can_configure_turbovec_with_pgvector_fallback() -> None:
    settings = Settings(
        _env_file=None,
        DATABASE_URL="sqlite+pysqlite:///:memory:",
        AION_DEFAULT_SEMANTIC_ADAPTER="turbovec",
        AION_TURBOVEC_ENABLED=True,
        AION_TURBOVEC_FAIL_OPEN_TO_PGVECTOR=True,
        AION_GRAPH_MEMORY_ADAPTER="in_memory",
    )
    container = KernelContainer(settings)

    assert container.semantic_memory_service.active_adapter_name == "pgvector"
    assert (
        container.semantic_memory_service.fallback_reason
        == "turbovec_package_unavailable"
    )
