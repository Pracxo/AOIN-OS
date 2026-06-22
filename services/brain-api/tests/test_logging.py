"""Structured logging tests."""

from aion_brain.config import Settings
from aion_brain.logging import build_log_record


def test_build_log_record_includes_required_fields() -> None:
    """Structured log records include AION metadata and optional trace fields."""
    settings = Settings(env="test", service_name="aion-test-api")

    record = build_log_record(
        "ready",
        level="debug",
        settings=settings,
        trace_id="trace-1",
        correlation_id="correlation-1",
        fields={"component": "health"},
    )

    assert record == {
        "service": "aion-test-api",
        "env": "test",
        "level": "DEBUG",
        "message": "ready",
        "trace_id": "trace-1",
        "correlation_id": "correlation-1",
        "component": "health",
    }
