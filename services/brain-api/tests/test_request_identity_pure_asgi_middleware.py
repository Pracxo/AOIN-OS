from __future__ import annotations

import asyncio
import inspect
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from aion_brain.api_support.middleware import RequestContextMiddleware
from aion_brain.contracts.api import RequestContext
from aion_brain.production_auth.request_middleware import (
    ProductionAuthRequestIdentityMiddleware,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXED_NOW = datetime(2026, 7, 16, 10, 0, 0, tzinfo=UTC)


def _context() -> RequestContext:
    return RequestContext(
        request_id="request-asgi",
        trace_id="trace-asgi",
        correlation_id="corr-asgi",
        actor_id="actor-not-trusted",
        workspace_id="workspace-not-used",
        idempotency_key="idem-not-used",
        method="POST",
        path="/ignored",
        started_at=FIXED_NOW,
        metadata={"safe": True},
    )


def test_request_identity_middleware_is_pure_asgi_class() -> None:
    source = (
        REPO_ROOT
        / "services/brain-api/src/aion_brain/production_auth/request_middleware.py"
    ).read_text()

    assert not issubclass(ProductionAuthRequestIdentityMiddleware, BaseHTTPMiddleware)
    assert "__call__" in ProductionAuthRequestIdentityMiddleware.__dict__
    assert "dispatch(" not in source
    assert "BaseHTTPMiddleware" not in source
    assert "Request(" not in source
    assert "Response(" not in source
    assert 'scope["headers"]' not in source
    assert 'scope["query_string"]' not in source
    assert 'scope["client"]' not in source
    assert 'scope["server"]' not in source
    assert inspect.iscoroutinefunction(ProductionAuthRequestIdentityMiddleware.__call__)


def test_pure_asgi_http_flow_attaches_disabled_evidence() -> None:
    seen: dict[str, object] = {}

    async def downstream(scope, receive, send) -> None:  # noqa: ANN001
        state = scope["state"]
        seen["failed"] = state["aion_request_identity_boundary_failed"]
        seen["failure_reason"] = state["aion_request_identity_boundary_failure_reason"]
        seen["attached"] = state["aion_request_identity_boundary_attached"]
        seen["request_id"] = state["aion_request_identity_context"].request_id
        seen["actor_id"] = state["aion_request_identity_context"].actor_id
        seen["bundle_request_id"] = state["aion_request_identity_boundary_bundle"].request_id
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b"", "more_body": False})

    middleware = ProductionAuthRequestIdentityMiddleware(downstream)
    scope = {"type": "http", "state": {"aion_request_context": _context()}}
    messages: list[dict[str, object]] = []

    async def receive() -> dict[str, object]:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict[str, object]) -> None:
        messages.append(message)

    asyncio.run(middleware(scope, receive, send))

    assert seen == {
        "failed": False,
        "failure_reason": None,
        "attached": True,
        "request_id": "request-asgi",
        "actor_id": None,
        "bundle_request_id": "request-asgi",
    }
    assert messages == [
        {"type": "http.response.start", "status": 204, "headers": []},
        {"type": "http.response.body", "body": b"", "more_body": False},
    ]


def test_request_context_executes_before_identity_and_endpoint() -> None:
    app = FastAPI()
    app.add_middleware(ProductionAuthRequestIdentityMiddleware)
    app.add_middleware(RequestContextMiddleware)

    @app.get("/test/order")
    def order(request: Request) -> dict[str, object]:
        context = request.state.aion_request_context
        verification = request.state.aion_request_identity_verification
        identity = request.state.aion_request_identity_context
        audit = request.state.aion_request_identity_audit_event
        provenance = request.state.aion_request_identity_provenance
        bundle = request.state.aion_request_identity_boundary_bundle
        return {
            "context_before_endpoint": True,
            "identity_before_endpoint": True,
            "request_ids_match": {
                context.request_id,
                verification.request_id,
                identity.request_id,
                audit.request_id,
                provenance.request_id,
                bundle.request_id,
            }
            == {context.request_id},
            "trace_match": verification.trace_id == context.trace_id,
            "correlation_match": verification.correlation_id == context.correlation_id,
            "authenticated": identity.authenticated,
        }

    response = TestClient(app).get(
        "/test/order",
        headers={
            "X-AION-Trace-ID": "trace-order",
            "X-AION-Correlation-ID": "corr-order",
            "X-AION-Actor-ID": "actor-ignored",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "context_before_endpoint": True,
        "identity_before_endpoint": True,
        "request_ids_match": True,
        "trace_match": True,
        "correlation_match": True,
        "authenticated": False,
    }
    assert "set-cookie" not in response.headers
    assert "www-authenticate" not in response.headers
