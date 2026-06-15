"""Kernel-owned API support route tests."""

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_api_request_record_endpoint_works() -> None:
    client = TestClient(create_app(kernel_container()))
    response = client.get("/health", headers={"X-AION-Correlation-ID": "corr-api"})
    request_id = response.headers["X-AION-Request-ID"]

    record_response = client.get(f"/brain/api/requests/{request_id}")

    assert record_response.status_code == 200
    assert record_response.json()["correlation_id"] == "corr-api"


def test_api_request_records_endpoint_works() -> None:
    client = TestClient(create_app(kernel_container()))
    client.get("/health", headers={"X-AION-Correlation-ID": "corr-list"})

    response = client.get("/brain/api/requests?correlation_id=corr-list")

    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_error_codes_endpoint_works() -> None:
    response = TestClient(create_app(kernel_container())).get("/brain/api/error-codes")

    assert response.status_code == 200
    assert "AION_INTERNAL_ERROR" in response.json()


def test_openapi_hygiene_endpoint_works() -> None:
    response = TestClient(create_app(kernel_container())).get("/brain/api/openapi-hygiene")

    assert response.status_code == 200
    assert "violations" in response.json()


def test_kernel_diagnostics_include_api_support_checks() -> None:
    container = kernel_container()

    check_names = {check.name for check in container.diagnostics.run()}

    assert "api_request_context_middleware_present" in check_names
    assert "api_exception_handlers_present" in check_names
    assert "api_request_audit_enabled" in check_names
    assert "api_openapi_hygiene_enabled" in check_names
