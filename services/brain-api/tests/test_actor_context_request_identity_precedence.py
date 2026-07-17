"""AION-160 RequestIdentityContext precedence tests."""

from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

from aion_brain.api_support.middleware import RequestContextMiddleware
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.production_auth.request_middleware import ProductionAuthRequestIdentityMiddleware


def test_valid_disabled_request_identity_takes_precedence_and_remains_anonymous() -> None:
    app = FastAPI()
    app.dependency_overrides[get_settings] = lambda: Settings(
        env="production",
        dev_auth_enabled=True,
    )
    app.add_middleware(ProductionAuthRequestIdentityMiddleware)
    app.add_middleware(RequestContextMiddleware)

    @app.get("/actor")
    def actor(
        request: Request,
        actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    ) -> dict[str, object]:
        bundle = request.state.aion_actor_context_resolution
        return {
            "actor_id": actor_context.actor_id,
            "workspace_id": actor_context.workspace_id,
            "roles": actor_context.roles,
            "permissions": actor_context.permissions,
            "security_scope": actor_context.security_scope,
            "dev_mode": actor_context.dev_mode,
            "source": bundle.source,
            "failed": request.state.aion_actor_context_resolution_failed,
        }

    response = TestClient(app).get(
        "/actor",
        headers={
            "X-AION-Actor-ID": "root",
            "X-AION-Workspace-ID": "system",
            "X-AION-Roles": "owner,admin",
            "X-AION-Permissions": "*",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "actor_id": None,
        "workspace_id": None,
        "roles": [],
        "permissions": [],
        "security_scope": [],
        "dev_mode": False,
        "source": "request_identity_disabled",
        "failed": False,
    }
