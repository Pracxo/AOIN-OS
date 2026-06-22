"""Workspace API tests."""

from fastapi.testclient import TestClient

from aion_brain.api.dependencies import get_identity_service
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.main import app
from tests.test_identity_contracts import make_membership, make_workspace
from tests.test_identity_service import FakeIdentityRepository, make_service


def test_workspace_and_membership_apis_work() -> None:
    """Workspace endpoints expose workspaces and memberships."""
    repository = FakeIdentityRepository()
    service = make_service(repository)
    app.dependency_overrides[get_identity_service] = lambda: service
    app.dependency_overrides[get_actor_context] = lambda: ActorContext(
        actor_id="actor-1",
        workspace_id="workspace-1",
        roles=["owner"],
        permissions=[],
        security_scope=["workspace:workspace-1"],
        dev_mode=True,
    )
    try:
        client = TestClient(app)
        created = client.post("/brain/workspaces", json=make_workspace().model_dump(mode="json"))
        fetched = client.get("/brain/workspaces/workspace-1")
        listed = client.get("/brain/workspaces")
        membership = client.post(
            "/brain/workspaces/workspace-1/memberships",
            json=make_membership().model_dump(mode="json"),
        )
        memberships = client.get("/brain/workspaces/workspace-1/memberships")
        revoked = client.post(
            "/brain/workspaces/workspace-1/memberships/membership-1/revoke",
            json={"reason": "test"},
        )
        archived = client.post(
            "/brain/workspaces/workspace-1/archive",
            json={"reason": "done"},
        )
    finally:
        app.dependency_overrides.clear()

    assert created.status_code == 200
    assert fetched.status_code == 200
    assert listed.status_code == 200
    assert membership.status_code == 200
    assert memberships.status_code == 200
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"
