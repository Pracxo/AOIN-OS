"""Shared local fakes for kernel assembly tests."""

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.config import Settings
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.kernel.container import KernelContainer
from aion_brain.kernel.repository import KernelRepository


class AllowPolicy:
    """Always-allow local policy fake."""

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=True,
            approval_required=False,
            reason="test_allowed",
            constraints=[],
            audit_level="standard",
        )


class FakeTelemetry:
    """Collect emitted kernel telemetry."""

    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


def kernel_container() -> KernelContainer:
    """Return a fully assembled local-only test container."""
    settings = Settings(
        _env_file=None,
        DATABASE_URL="sqlite+pysqlite:///:memory:",
        AION_DEFAULT_SEMANTIC_ADAPTER="in_memory",
        AION_GRAPH_MEMORY_ADAPTER="in_memory",
    )
    repository = KernelRepository(
        engine=create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        ),
        best_effort=False,
    )
    return KernelContainer(
        settings,
        kernel_repository=repository,
        policy_adapter=AllowPolicy(),
        telemetry_service=FakeTelemetry(),
    )
