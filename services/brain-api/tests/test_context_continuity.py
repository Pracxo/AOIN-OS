from __future__ import annotations

from aion_brain.contracts.situations import ContextContinuityRequest
from tests.situation_helpers import bundle


def test_context_continuity_records_carried_and_dropped_refs() -> None:
    services = bundle()
    record = services.continuity_service.record(
        ContextContinuityRequest(
            owner_scope=["workspace:main"],
            refs=["goal-1", "stale-memory-1"],
            continuity_type="dialogue_turn",
        )
    )

    assert record.status == "warning"
    assert "goal-1" in record.carried_refs
    assert "stale-memory-1" in record.dropped_refs
    listed = services.continuity_service.list_records(scope=["workspace:main"])
    assert listed[0].continuity_id == record.continuity_id
