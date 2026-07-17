"""AION-160 actor-context audit and provenance tests."""

from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

from aion_brain.api_support.middleware import RequestContextMiddleware
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context


def test_request_state_contains_redacted_resolution_evidence() -> None:
    app = FastAPI()
    app.dependency_overrides[get_settings] = lambda: Settings(env="production")
    app.add_middleware(RequestContextMiddleware)

    @app.get("/evidence")
    def evidence(
        request: Request,
        actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    ) -> dict[str, object]:
        audit = request.state.aion_actor_context_resolution_audit_event
        provenance = request.state.aion_actor_context_resolution_provenance
        return {
            "actor_id": actor_context.actor_id,
            "source": request.state.aion_actor_context_resolution_source,
            "failed": request.state.aion_actor_context_resolution_failed,
            "failure_reason": request.state.aion_actor_context_resolution_failure_reason,
            "audit_values_stored": audit.production_identity_header_values_stored,
            "provenance_raw_request": provenance.resolver_input_contains_raw_request,
            "provenance_headers": provenance.resolver_input_contains_headers,
        }

    response = TestClient(app).get(
        "/evidence",
        headers={"X-AION-Actor-ID": "root", "X-AION-Permissions": "*"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "actor_id": None,
        "source": "anonymous_fail_closed",
        "failed": False,
        "failure_reason": None,
        "audit_values_stored": False,
        "provenance_raw_request": False,
        "provenance_headers": False,
    }
