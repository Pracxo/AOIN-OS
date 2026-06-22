"""Working memory API tests."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.api.working_memory import get_working_memory_service
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.working_memory import WorkingMemorySlot
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.main import app


class FakeWorkingMemoryService:
    def write_slot(self, request):
        return slot(slot_id=request.slot_id or "slot-api", owner_scope=request.owner_scope)

    def query_slots(self, query):
        return [slot(slot_id="slot-api", owner_scope=query.scope)]

    def get_slot(self, slot_id, scope):
        return slot(slot_id=slot_id, owner_scope=scope)

    def pin_slot(self, slot_id, scope):
        return slot(slot_id=slot_id, owner_scope=scope, pinned=True)

    def unpin_slot(self, slot_id, scope):
        return slot(slot_id=slot_id, owner_scope=scope, pinned=False)

    def delete_slot(self, slot_id, scope):
        return True

    def sweep_expired(self, scope, limit=100):
        return {"swept": 1, "slot_ids": ["slot-api"]}


def test_working_memory_api_routes_work() -> None:
    """Working memory routes return public contracts."""
    app.dependency_overrides[get_working_memory_service] = lambda: FakeWorkingMemoryService()
    app.dependency_overrides[get_actor_context] = actor_context
    try:
        client = TestClient(app)
        write = client.post(
            "/brain/working-memory",
            json={
                "slot_type": "recent_event",
                "source_type": "event",
                "content": {"event_id": "event-1"},
                "summary": "Event received",
            },
        )
        query = client.post(
            "/brain/working-memory/query",
            json={"scope": ["workspace:main"]},
        )
        get = client.get("/brain/working-memory/slot-api", params={"scope": "workspace:main"})
        pin = client.post("/brain/working-memory/slot-api/pin", params={"scope": "workspace:main"})
        unpin = client.post(
            "/brain/working-memory/slot-api/unpin",
            params={"scope": "workspace:main"},
        )
        delete = client.delete(
            "/brain/working-memory/slot-api",
            params={"scope": "workspace:main"},
        )
        sweep = client.post(
            "/brain/working-memory/sweep-expired",
            json={"scope": ["workspace:main"]},
        )
    finally:
        app.dependency_overrides.clear()

    for response in (write, query, get, pin, unpin, delete, sweep):
        assert response.status_code == 200
    assert write.json()["slot_id"] == "slot-api"
    assert pin.json()["pinned"] is True
    assert delete.json()["deleted"] is True
    assert sweep.json()["swept"] == 1


def slot(**updates: object) -> WorkingMemorySlot:
    payload = {
        "slot_id": "slot-1",
        "focus_session_id": None,
        "trace_id": "trace-1",
        "actor_id": "actor-1",
        "workspace_id": "workspace-1",
        "slot_type": "recent_event",
        "source_type": "event",
        "source_id": "event-1",
        "content": {"event_id": "event-1"},
        "summary": "Event received",
        "priority": 0.5,
        "confidence": 0.8,
        "ttl_seconds": None,
        "expires_at": None,
        "pinned": False,
        "owner_scope": ["workspace:main"],
        "metadata": {},
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
        "deleted_at": None,
    }
    payload.update(updates)
    return WorkingMemorySlot.model_validate(payload)


def actor_context() -> ActorContext:
    return ActorContext(
        actor_id="actor-1",
        workspace_id="workspace-1",
        roles=["owner"],
        permissions=["trace.read"],
        security_scope=["workspace:main"],
        dev_mode=True,
    )
