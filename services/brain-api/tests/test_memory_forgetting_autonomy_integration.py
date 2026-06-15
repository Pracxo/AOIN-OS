"""Memory forgetting autonomy integration tests."""

from aion_brain.contracts.memory_governance import ForgetMemoryRequest
from tests.autonomy_fakes import FakeAutonomyGovernor
from tests.test_memory_governance import make_forgetting_service, make_memory_service, memory


def test_memory_forgetting_blocks_when_autonomy_denies() -> None:
    """Approved forget requests still pass through autonomy before mutation."""
    memory_service, semantic_adapter = make_memory_service()
    memory_service.create(memory("memory-1"))
    service = make_forgetting_service(memory_service, semantic_adapter)
    service._autonomy_governor = FakeAutonomyGovernor(allow=False)  # noqa: SLF001

    result = service.forget(
        ForgetMemoryRequest(
            target_type="memory",
            target_id="memory-1",
            owner_scope=["workspace:main"],
            reason="approved cleanup",
            approval_present=True,
        )
    )

    assert result.status == "blocked_by_policy"
    assert memory_service.get("memory-1") is not None
