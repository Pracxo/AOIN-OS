from __future__ import annotations

from aion_brain.contracts.situations import SituationCreateRequest
from aion_brain.contracts.temporal_state import StateAtomCreateRequest
from tests.situation_helpers import bundle


def test_situation_services_emit_visual_telemetry_events() -> None:
    services = bundle()
    services.situation_service.create(
        SituationCreateRequest(
            title="Current state",
            summary="Generic state.",
            owner_scope=["workspace:main"],
        )
    )
    services.state_atom_service.create(
        StateAtomCreateRequest(
            source_id="source-1",
            predicate="status",
            value={"status": "active"},
            owner_scope=["workspace:main"],
        )
    )

    event_types = {getattr(event, "event_type", "") for event in services.telemetry.events}
    assert "situation_created" in event_types
    assert "state_atom_created" in event_types
