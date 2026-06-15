"""Module runtime repository tests."""

from datetime import UTC, datetime

from sqlalchemy import create_engine

from aion_brain.contracts.modules import (
    CapabilityRuntimeBinding,
    ModuleHealthCheck,
    ModuleRuntime,
)
from aion_brain.modules.repository import ModuleRuntimeRepository


def test_module_runtime_repository_persists_runtime_binding_and_health() -> None:
    """Repository persists runtime, binding, and health records without Docker."""
    repository = ModuleRuntimeRepository(engine=create_engine("sqlite+pysqlite:///:memory:"))
    runtime = ModuleRuntime(
        runtime_id="runtime-1",
        module_id="test.module",
        version="0.1.0",
        runtime_type="local_internal",
        endpoint_ref=None,
        status="active",
        health_status="unknown",
        config={},
    )
    binding = CapabilityRuntimeBinding(
        binding_id="binding-1",
        capability_id="aion.internal.noop",
        module_id="test.module",
        runtime_id="runtime-1",
        invocation_mode="controlled",
        status="active",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    health = ModuleHealthCheck(
        health_check_id="health-1",
        runtime_id="runtime-1",
        module_id="test.module",
        status="healthy",
        latency_ms=1,
        details={"ok": True},
        created_at=datetime.now(UTC),
    )

    repository.save_runtime(runtime)
    repository.save_binding(binding)
    repository.save_health_check(health)
    repository.update_runtime_health("runtime-1", "healthy", health.created_at)

    assert repository.get_runtime("runtime-1").health_status == "healthy"  # type: ignore[union-attr]
    assert repository.list_runtimes()[0].runtime_id == "runtime-1"
    stored_binding = repository.get_active_binding("aion.internal.noop", "controlled")
    assert stored_binding is not None
    assert stored_binding.binding_id == binding.binding_id
    assert stored_binding.runtime_id == "runtime-1"
