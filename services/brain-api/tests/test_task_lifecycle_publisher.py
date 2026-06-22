"""Task lifecycle publisher tests."""

from aion_brain.contracts.tasks import TaskLifecycleEvent
from aion_brain.tasks.publisher import NoopTaskLifecyclePublisher, _subject


def test_noop_lifecycle_publisher_records_even_when_configured_failure() -> None:
    """The noop publisher can simulate NATS failure without throwing."""
    event = make_event("task_run_completed")
    publisher = NoopTaskLifecyclePublisher(published=False)

    published = publisher.publish(event)

    assert published is False
    assert publisher.events == [event]


def test_lifecycle_subjects_are_generic() -> None:
    """Lifecycle events publish to generic goal, task, or schedule subjects."""
    assert _subject(make_event("goal_created")) == "aion.lifecycle.goals"
    assert _subject(make_event("task_created")) == "aion.lifecycle.tasks"
    assert _subject(make_event("schedule_created")) == "aion.lifecycle.schedules"


def make_event(event_type: str) -> TaskLifecycleEvent:
    """Create a lifecycle event."""
    return TaskLifecycleEvent(
        lifecycle_event_id=f"lifecycle-{event_type}",
        task_id="task-1",
        goal_id="goal-1",
        trace_id="trace-1",
        event_type=event_type,  # type: ignore[arg-type]
        payload={},
    )
