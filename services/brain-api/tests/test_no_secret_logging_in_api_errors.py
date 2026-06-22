"""Secret redaction tests for API errors."""

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from aion_brain.api_support.exception_handlers import register_exception_handlers
from aion_brain.api_support.middleware import RequestContextMiddleware


def test_error_detail_does_not_expose_secrets() -> None:
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)
    register_exception_handlers(app)

    @app.get("/secret")
    def secret() -> None:
        raise HTTPException(status_code=400, detail={"api_key": "sk-test", "ok": "visible"})

    response = TestClient(app).get("/secret")
    text = response.text.lower()

    assert "api_key" not in text
    assert "sk-test" not in text
    assert response.json()["error"]["detail"]["ok"] == "visible"
