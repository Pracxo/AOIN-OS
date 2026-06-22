"""Model gateway visual telemetry tests."""

from tests.model_gateway_fakes import gateway_request, model_gateway_service
from tests.model_outputs_fakes import governance_service


def test_visual_telemetry_emits_model_gateway_events() -> None:
    service, _, _, telemetry = model_gateway_service()
    service.complete(gateway_request())

    event_types = {event.event_type for event in telemetry.events}
    assert "model_gateway_requested" in event_types
    assert "model_route_selected" in event_types
    assert "model_call_recorded" in event_types
    assert "model_usage_recorded" in event_types


def test_model_gateway_records_output_governance_metadata() -> None:
    service, _, _, _ = model_gateway_service()
    governance, _, _, _ = governance_service()
    service.set_output_governance_service(governance)

    response = service.complete(gateway_request())

    assert "model_output_id" in response.output
    assert response.output["output_governance_status"] in {"passed", "warning", "blocked"}
