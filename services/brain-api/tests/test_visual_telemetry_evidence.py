"""Evidence visual telemetry tests."""

from tests.test_evidence_service import FakeTelemetryService, make_ingest_request, make_service


def test_visual_telemetry_emits_evidence_events() -> None:
    """Evidence service emits evidence and chunk events."""
    telemetry = FakeTelemetryService()
    service = make_service(telemetry=telemetry)

    service.ingest(make_ingest_request(content_text="alpha beta " * 120))

    event_types = [event.event_type for event in telemetry.events]
    assert "evidence_created" in event_types
    assert "evidence_chunk_created" in event_types

