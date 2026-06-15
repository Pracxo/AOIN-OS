"""Request context middleware tests."""

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_request_context_middleware_sets_request_id() -> None:
    response = TestClient(create_app(kernel_container())).get("/health")

    assert response.headers["X-AION-Request-ID"].startswith("request-")


def test_request_context_middleware_propagates_correlation_id() -> None:
    response = TestClient(create_app(kernel_container())).get(
        "/health",
        headers={"X-AION-Correlation-ID": "corr-test"},
    )

    assert response.headers["X-AION-Correlation-ID"] == "corr-test"


def test_request_context_middleware_propagates_trace_id() -> None:
    response = TestClient(create_app(kernel_container())).get(
        "/health",
        headers={"X-AION-Trace-ID": "trace-test"},
    )

    assert response.headers["X-AION-Trace-ID"] == "trace-test"


def test_request_context_middleware_extracts_idempotency_key_header() -> None:
    client = TestClient(create_app(kernel_container()))
    response = client.get("/health", headers={"X-AION-Idempotency-Key": "idem-test"})
    request_id = response.headers["X-AION-Request-ID"]

    record = client.get(f"/brain/api/requests/{request_id}").json()

    assert record["idempotency_key"] == "idem-test"


def test_response_headers_include_aion_request_id() -> None:
    response = TestClient(create_app(kernel_container())).get("/health")

    assert "X-AION-Request-ID" in response.headers
    assert response.headers["X-AION-Version"] == "v0.1"


def test_visual_telemetry_emits_api_request_events() -> None:
    container = kernel_container()
    client = TestClient(create_app(container))

    client.get("/health")

    event_types = {
        getattr(event, "event_type", None) for event in container.telemetry_service.events
    }
    assert "api_request_started" in event_types
    assert "api_request_completed" in event_types
