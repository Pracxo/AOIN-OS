"""Public error response leakage tests."""

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from aion_brain.api_support.exception_handlers import register_exception_handlers
from aion_brain.api_support.middleware import RequestContextMiddleware


def test_no_raw_sql_or_provider_object_appears_in_error_response() -> None:
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)
    register_exception_handlers(app)

    class OpenAIResponse:
        pass

    @app.get("/unsafe")
    def unsafe() -> None:
        raise HTTPException(
            status_code=400,
            detail={
                "sql": "SELECT * FROM aion_events",
                "provider_response": OpenAIResponse(),
            },
        )

    response = TestClient(app).get("/unsafe")
    text = response.text.lower()

    assert "select *" not in text
    assert "openai" not in text
    assert "provider_response" not in text


def test_generic_error_does_not_leak_stacktrace() -> None:
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)
    register_exception_handlers(app)

    @app.get("/boom")
    def boom() -> None:
        raise RuntimeError("Traceback File secret")

    response = TestClient(app, raise_server_exceptions=False).get("/boom")

    assert "traceback" not in response.text.lower()
    assert response.json()["error"]["message"] == "An internal AION error occurred."
