"""Replay and regression visual telemetry tests."""

from aion_brain.replay.snapshot import _emit


class Telemetry:
    def __init__(self) -> None:
        self.events = []

    def emit(self, event) -> None:
        self.events.append(event)


def test_replay_snapshot_and_regression_event_types_are_valid() -> None:
    """New cognitive replay telemetry remains frontend-agnostic."""
    telemetry = Telemetry()
    for event_type, node_type in (
        ("snapshot_created", "snapshot"),
        ("replay_completed", "replay"),
        ("regression_run_completed", "regression"),
        ("eval_adapter_run", "eval"),
    ):
        _emit(
            telemetry,
            event_type,
            node_type,
            f"{node_type}-1",
            "trace-1",
            ["workspace:main"],
            0.5,
        )
    assert [event.node_type for event in telemetry.events] == [
        "snapshot",
        "replay",
        "regression",
        "eval",
    ]
