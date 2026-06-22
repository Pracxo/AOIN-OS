"""AION exception handler tests."""

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

from aion_brain.api_support.errors import AIONConflictException
from aion_brain.api_support.exception_handlers import register_exception_handlers
from aion_brain.api_support.middleware import RequestContextMiddleware
from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


class Payload(BaseModel):
    value: int


def _app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)
    register_exception_handlers(app)

    @app.post("/validate")
    def validate(payload: Payload) -> dict[str, Any]:
        return payload.model_dump()

    @app.get("/aion")
    def aion_error() -> None:
        raise AIONConflictException("Conflict")

    @app.get("/generic")
    def generic_error() -> None:
        raise RuntimeError("Traceback secret SELECT * FROM users")

    @app.get("/http")
    def http_error() -> None:
        raise HTTPException(
            status_code=400,
            detail={"sql": "SELECT * FROM records", "api_key": "secret"},
        )

    return app


def test_validation_error_returns_aion_error_response() -> None:
    response = TestClient(_app()).post("/validate", json={"value": "bad"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "AION_VALIDATION_ERROR"


def test_aion_exception_returns_aion_error_response() -> None:
    response = TestClient(_app()).get("/aion")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "AION_CONFLICT"


def test_generic_exception_does_not_expose_stack_trace() -> None:
    response = TestClient(_app(), raise_server_exceptions=False).get("/generic")
    text = response.text.lower()

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "AION_INTERNAL_ERROR"
    assert "traceback" not in text
    assert "select *" not in text


def test_http_error_detail_is_sanitized() -> None:
    response = TestClient(_app()).get("/http")
    text = response.text.lower()

    assert response.status_code == 400
    assert "select *" not in text
    assert "api_key" not in text
    assert "secret" not in text


def test_unknown_route_returns_aion_error_response() -> None:
    response = TestClient(_app()).get("/missing")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "AION_ROUTE_NOT_FOUND"


def test_visual_telemetry_emits_api_error_event() -> None:
    container = kernel_container()
    app = create_app(container)

    @app.get("/api-error-test", tags=["test"])
    def api_error_test() -> None:
        raise HTTPException(status_code=400, detail={"reason": "bad"})

    response = TestClient(app).get("/api-error-test")
    event_types = {
        getattr(event, "event_type", None) for event in container.telemetry_service.events
    }

    assert response.status_code == 400
    assert "api_error_recorded" in event_types
