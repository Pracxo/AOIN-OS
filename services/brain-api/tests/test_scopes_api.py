"""Scope API tests."""

from fastapi.testclient import TestClient

from aion_brain.api.dependencies import get_scope_resolver
from aion_brain.contracts.scopes import ActorContext, ScopeResolution, ScopeResolutionRequest
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.main import app


class FakeScopeResolver:
    """Scope resolver fake."""

    def resolve(
        self,
        request: ScopeResolutionRequest,
        actor_context: ActorContext,
    ) -> ScopeResolution:
        return ScopeResolution(
            scope_resolution_id="scope-resolution-1",
            actor_id=actor_context.actor_id,
            workspace_id=actor_context.workspace_id,
            requested_scopes=request.requested_scopes,
            resolved_scopes=actor_context.security_scope,
            permissions=actor_context.permissions,
            allow=True,
            constraints=[],
            created_at=None,
        )


def test_scope_resolve_api_works() -> None:
    """Scope resolve endpoint returns ScopeResolution."""
    app.dependency_overrides[get_scope_resolver] = lambda: FakeScopeResolver()
    app.dependency_overrides[get_actor_context] = lambda: ActorContext(
        actor_id="actor-1",
        workspace_id="workspace-1",
        roles=["owner"],
        permissions=["memory.read"],
        security_scope=["workspace:workspace-1"],
        dev_mode=True,
    )
    try:
        response = TestClient(app).post(
            "/brain/scopes/resolve",
            json={
                "actor_id": "actor-1",
                "workspace_id": "workspace-1",
                "requested_scopes": ["workspace:workspace-1"],
                "action_type": "memory.retrieve",
                "resource_type": "memory",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["allow"] is True
    assert response.json()["actor_id"] == "actor-1"
