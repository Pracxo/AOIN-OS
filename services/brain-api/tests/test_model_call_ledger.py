"""Model call ledger repository tests."""

from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.contracts.reasoning import ModelCallRecord
from aion_brain.reasoning.repository import ReasoningRepository


def test_model_call_ledger_persists_records() -> None:
    """ReasoningRepository saves and returns model call records."""
    repository = ReasoningRepository(engine=make_engine())
    record = ModelCallRecord(
        model_call_id="model-call-1",
        trace_id="trace-1",
        reasoning_id="reasoning-1",
        provider="aion-local",
        model="deterministic-reasoner-v0",
        mode="analyze",
        request={"prompt": "provider-neutral"},
        response={"summary": "summary"},
        status="completed",
        latency_ms=0,
        cost_estimate=0.0,
        created_at=datetime.now(UTC),
    )

    repository.save_model_call(record)
    persisted = repository.get_model_call("model-call-1")

    assert persisted is not None
    assert persisted.model_call_id == "model-call-1"
    assert persisted.provider == "aion-local"


def make_engine() -> object:
    """Create an isolated SQLite engine."""
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
