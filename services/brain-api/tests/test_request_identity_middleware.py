from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from aion_brain.api_support.middleware import RequestContextMiddleware
from aion_brain.production_auth.request_middleware import ProductionAuthRequestIdentityMiddleware


def test_request_identity_middleware_attaches_disabled_context_after_request_context() -> None:
    app = FastAPI()
    app.add_middleware(ProductionAuthRequestIdentityMiddleware)
    app.add_middleware(RequestContextMiddleware)

    @app.get("/identity-state")
    def identity_state(request: Request) -> dict[str, object]:
        context = request.state.aion_request_identity_context
        verification = request.state.aion_request_identity_verification
        return {
            "request_context_present": hasattr(request.state, "aion_request_context"),
            "request_id_match": context.request_id
            == request.state.aion_request_context.request_id,
            "authenticated": verification.authenticated,
            "actor_id": verification.actor_id,
            "roles": list(verification.roles),
            "runtime_effect": verification.runtime_effect,
            "failed": request.state.aion_request_identity_boundary_failed,
        }

    response = TestClient(app).get(
        "/identity-state",
        headers={
            "Authorization": "Bearer ignored",
            "Cookie": "ignored=true",
            "X-AION-Actor-ID": "legacy-actor",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "request_context_present": True,
        "request_id_match": True,
        "authenticated": False,
        "actor_id": None,
        "roles": [],
        "runtime_effect": False,
        "failed": False,
    }
    assert "set-cookie" not in response.headers
    assert "www-authenticate" not in response.headers


def test_request_identity_middleware_missing_context_fails_closed_and_continues() -> None:
    app = FastAPI()
    app.add_middleware(ProductionAuthRequestIdentityMiddleware)

    @app.get("/available")
    def available(request: Request) -> dict[str, object]:
        return {
            "failed": request.state.aion_request_identity_boundary_failed,
            "failure_reason": request.state.aion_request_identity_boundary_failure_reason,
            "has_identity_context": hasattr(
                request.state,
                "aion_request_identity_context",
            ),
        }

    response = TestClient(app).get("/available")

    assert response.status_code == 200
    assert response.json() == {
        "failed": True,
        "failure_reason": "request_context_absent",
        "has_identity_context": False,
    }


def test_request_identity_middleware_source_does_not_access_http_material() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    source = Path(
        root / "services/brain-api/src/aion_brain/production_auth/request_middleware.py"
    ).read_text()

    assert "request.headers" not in source
    assert "request.cookies" not in source
    assert "request.query_params" not in source
    assert "request.body" not in source
