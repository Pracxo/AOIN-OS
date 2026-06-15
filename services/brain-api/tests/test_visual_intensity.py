"""Visual intensity helper tests."""

from datetime import UTC, datetime, timedelta

from aion_brain.visual.intensity import apply_time_decay, clamp_intensity, status_from_event_type


def test_clamp_intensity_clamps_values() -> None:
    """Intensity is always within the public contract range."""
    assert clamp_intensity(-2.0) == 0.0
    assert clamp_intensity(2.0) == 1.0


def test_apply_time_decay_reduces_old_intensity() -> None:
    """One half-life halves intensity."""
    now = datetime.now(UTC)
    assert apply_time_decay(1.0, now - timedelta(hours=1), now, 3600) == 0.5


def test_status_from_event_type_maps_blocked_events() -> None:
    """Blocked events project to blocked visual status."""
    assert status_from_event_type("execution_blocked") == "blocked"
    assert status_from_event_type("task_run_failed") == "failed"
    assert status_from_event_type("execution_completed") == "completed"
