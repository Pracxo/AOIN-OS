from __future__ import annotations

from aion_brain.contracts.grounding import GroundingSourceCreateRequest
from tests.grounding_helpers import service_bundle


def test_visual_telemetry_emits_grounding_events() -> None:
    bundle = service_bundle()

    source = bundle.source_service.create_source(
        GroundingSourceCreateRequest(
            source_type="generic",
            source_id="generic-1",
            title="Generic",
            summary="AION records deterministic source support.",
            owner_scope=["workspace:main"],
        )
    )
    bundle.mapper.map_text(
        text="AION records deterministic source support.",
        trace_id="trace-1",
        owner_scope=["workspace:main"],
        sources=[source],
        target_type="response",
        target_id="response-1",
    )

    event_types = {getattr(event, "event_type", "") for event in bundle.telemetry.events}
    assert "grounding_source_created" in event_types
    assert "citation_record_created" in event_types
    assert "citation_map_created" in event_types
