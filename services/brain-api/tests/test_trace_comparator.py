"""Deterministic trace comparison tests."""

from aion_brain.contracts.replay import BrainSnapshot
from aion_brain.replay.comparator import TraceComparator


def snapshot(snapshot_id: str, state: dict) -> BrainSnapshot:
    return BrainSnapshot(
        snapshot_id=snapshot_id,
        trace_id="trace-1",
        owner_scope=["workspace:main"],
        snapshot_type="full_trace",
        state=state,
        content_hash="hash",
    )


def test_comparator_ignores_identity_fields() -> None:
    """Default ignored fields do not create drift."""
    result = TraceComparator().compare(
        snapshot("source", {"trace_id": "trace-1", "outcome": {"status": "planned"}}),
        snapshot("replay", {"trace_id": "trace-2", "outcome": {"status": "planned"}}),
    )
    assert result.matched
    assert result.score == 1.0


def test_comparator_detects_plan_policy_and_outcome_drift() -> None:
    """Core semantic changes are high-severity drift."""
    source = snapshot(
        "source",
        {
            "plan": {"steps": [{"action_type": "memory.retrieve"}]},
            "policy": [{"allow": True}],
            "outcome": {"status": "planned"},
        },
    )
    replay = snapshot(
        "replay",
        {
            "plan": {"steps": [{"action_type": "memory.write"}]},
            "policy": [{"allow": False}],
            "outcome": {"status": "blocked_by_policy"},
        },
    )
    result = TraceComparator().compare(source, replay)
    assert result.drift_detected
    assert 0.0 <= result.score <= 1.0
    assert {item["reason"] for item in result.differences} >= {
        "plan_action_changed",
        "policy_outcome_changed",
        "outcome_status_changed",
    }
