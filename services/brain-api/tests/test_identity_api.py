"""Identity API tests."""

from fastapi.testclient import TestClient

from aion_brain.api.dependencies import get_identity_service
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.main import app
from tests.test_identity_contracts import make_actor, make_grant
from tests.test_identity_service import FakeIdentityRepository, make_service


def test_me_and_actor_permission_apis_work() -> None:
    """Identity endpoints expose actor context, actors, and permission grants."""
    repository = FakeIdentityRepository()
    service = make_service(repository)
    app.dependency_overrides[get_identity_service] = lambda: service
    app.dependency_overrides[get_actor_context] = lambda: ActorContext(
        actor_id="actor-1",
        workspace_id="workspace-1",
        roles=["owner"],
        permissions=["identity.actor.create"],
        security_scope=["workspace:workspace-1"],
        dev_mode=True,
    )
    try:
        client = TestClient(app)
        me = client.get("/brain/me")
        created = client.post(
            "/brain/identity/actors",
            json=make_actor().model_dump(mode="json"),
        )
        fetched = client.get("/brain/identity/actors/actor-1")
        listed = client.get("/brain/identity/actors")
        disabled = client.post(
            "/brain/identity/actors/actor-1/disable",
            json={"reason": "test"},
        )
        grant = client.post(
            "/brain/identity/permissions",
            json=make_grant().model_dump(mode="json"),
        )
        grants = client.get("/brain/identity/permissions", params={"actor_id": "actor-1"})
        revoked = client.post(
            "/brain/identity/permissions/grant-1/revoke",
            json={"reason": "test"},
        )
    finally:
        app.dependency_overrides.clear()

    assert me.status_code == 200
    assert me.json()["actor_id"] == "actor-1"
    assert created.status_code == 200
    assert fetched.status_code == 200
    assert listed.status_code == 200
    assert disabled.status_code == 200
    assert disabled.json()["status"] == "disabled"
    assert grant.status_code == 200
    assert grants.status_code == 200
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"
