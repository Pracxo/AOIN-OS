"""Replay contract validation tests."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.replay import BrainSnapshot, ReplayRequest, TraceComparison


def test_brain_snapshot_validates_type_and_nonempty_state() -> None:
    """Snapshots reject unknown types and empty state."""
    payload = {
        "snapshot_id": "snapshot-1",
        "owner_scope": ["workspace:main"],
        "snapshot_type": "full_trace",
        "state": {"trace": {}},
        "content_hash": "hash",
    }
    assert BrainSnapshot.model_validate(payload).snapshot_type == "full_trace"
    with pytest.raises(ValidationError):
        BrainSnapshot.model_validate({**payload, "snapshot_type": "unknown"})
    with pytest.raises(ValidationError):
        BrainSnapshot.model_validate({**payload, "state": {}})


def test_replay_request_and_comparison_validate_bounds() -> None:
    """Replay modes and comparison scores remain constrained."""
    request = ReplayRequest(source_trace_id="trace-1", owner_scope=["workspace:main"])
    assert request.mode == "dry_run"
    with pytest.raises(ValidationError):
        ReplayRequest(source_trace_id="trace-1", owner_scope=["workspace:main"], mode="controlled")
    with pytest.raises(ValidationError):
        TraceComparison(
            comparison_id="comparison-1",
            source_trace_id="trace-1",
            replay_trace_id=None,
            source_snapshot_id=None,
            replay_snapshot_id=None,
            matched=False,
            drift_detected=True,
            score=1.1,
            differences=[],
            ignored_fields=[],
            created_at=datetime.now(UTC),
        )
