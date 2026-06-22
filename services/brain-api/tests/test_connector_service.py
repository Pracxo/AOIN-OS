"""Connector service tests."""

from tests.sandbox_fakes import (
    FakeTelemetry,
    connector_request,
    make_connector_service,
    make_secret_service,
    secret_request,
)


def test_connector_service_creates_connector_metadata_only() -> None:
    telemetry = FakeTelemetry()
    service = make_connector_service(telemetry=telemetry)

    connector = service.create_connector(connector_request())

    assert connector.connector_id == "connector-1"
    assert connector.connector_type == "generic_placeholder"
    assert [event.event_type for event in telemetry.events] == ["connector_created"]


def test_connector_service_validate_does_not_perform_network_call() -> None:
    secret_service = make_secret_service()
    secret_service.create_secret_ref(secret_request())
    service = make_connector_service(secret_service=secret_service)
    service.create_connector(connector_request(auth_secret_ref_id="secret-ref-1"))

    result = service.validate_connector("connector-1", ["workspace:main"])

    assert result.status == "passed"
    assert "connector_no_network_call" in {check.check_id for check in result.checks}
