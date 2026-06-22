"""Local observability recorder tests."""

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.audit.repository import AuditRepository
from aion_brain.observability.local_recorder import LocalObservabilityRecorder
from aion_brain.observability.repository import ObservabilityRepository
from aion_brain.visual.repository import VisualRepository
from tests.test_observability_contracts import event
from tests.test_visual_service import telemetry


def test_local_observability_recorder_records_event_and_returns_summary() -> None:
    """The local recorder persists events and summarizes local telemetry."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    audit = AuditRepository(engine=engine)
    audit.save_visual_telemetry("trace-1", [telemetry()])
    repository = ObservabilityRepository(engine=engine)
    recorder = LocalObservabilityRecorder(repository, VisualRepository(engine=engine))

    recorded = recorder.record_event(event())
    summary = recorder.summarize(["workspace:main"])

    assert recorded.created_at is not None
    assert summary.observability_event_count == 1
    assert summary.telemetry_event_count == 1
    assert summary.trace_count == 1
