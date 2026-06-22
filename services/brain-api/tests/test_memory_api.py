"""Memory API tests."""

from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient

from aion_brain.api.memory import get_memory_service
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.main import app
from aion_brain.memory.in_memory_adapter import InMemorySemanticMemoryAdapter
from aion_brain.memory.service import PostgresMemoryService


class FakePolicyAdapter:
    """Fake policy adapter for memory API tests."""

    def __init__(self, *, allow: bool = True) -> None:
        self.allow = allow
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        return PolicyDecision(
            decision_id="decision-1",
            trace_id=request.trace_id or "",
            allow=self.allow,
            approval_required=False,
            reason="allowed" if self.allow else "denied",
            constraints=[] if self.allow else ["blocked"],
            audit_level="standard",
        )


@pytest.fixture
def memory_service() -> PostgresMemoryService:
    """Create a memory service for API tests."""
    return PostgresMemoryService(InMemorySemanticMemoryAdapter(), FakePolicyAdapter())


@pytest.fixture
def client(memory_service: PostgresMemoryService) -> TestClient:
    """Create a test client with memory dependencies overridden."""
    app.dependency_overrides[get_memory_service] = lambda: memory_service
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def memory_payload(memory_id: str = "memory-1", summary: str = "alpha beta") -> dict[str, Any]:
    """Return a valid memory payload."""
    return {
        "memory_id": memory_id,
        "memory_type": "semantic",
        "owner_scope": ["workspace:main"],
        "source_event_id": None,
        "content_ref": "content://memory-1",
        "summary": summary,
        "confidence": 0.9,
        "sensitivity": "low",
        "created_at": datetime.now(UTC).isoformat(),
        "expires_at": None,
        "metadata": {"source": "test"},
    }


def test_memory_api_create_and_get(client: TestClient) -> None:
    """Memory API creates and returns a memory record."""
    create_response = client.post("/brain/memory", json=memory_payload())
    get_response = client.get("/brain/memory/memory-1")

    assert create_response.status_code == 200
    assert create_response.json()["memory_id"] == "memory-1"
    assert get_response.status_code == 200
    assert get_response.json()["summary"] == "alpha beta"


def test_memory_api_retrieve_and_delete(client: TestClient) -> None:
    """Memory API retrieves lexically and excludes deleted records."""
    client.post("/brain/memory", json=memory_payload("memory-1", "alpha beta"))
    client.post("/brain/memory", json=memory_payload("memory-2", "delta epsilon"))

    retrieve_response = client.post(
        "/brain/memory/retrieve",
        json={
            "query": "alpha",
            "scope": ["workspace:main"],
            "limit": 10,
            "memory_types": [],
        },
    )
    delete_response = client.delete("/brain/memory/memory-1")
    retrieve_after_delete = client.post(
        "/brain/memory/retrieve",
        json={
            "query": "alpha",
            "scope": ["workspace:main"],
            "limit": 10,
            "memory_types": [],
        },
    )

    assert retrieve_response.status_code == 200
    assert [record["memory_id"] for record in retrieve_response.json()][0] == "memory-1"
    assert delete_response.status_code == 200
    assert delete_response.json() == {"deleted": True, "memory_id": "memory-1"}
    assert [record["memory_id"] for record in retrieve_after_delete.json()] == ["memory-2"]


def test_memory_api_policy_deny_blocks_write() -> None:
    """Policy denial blocks memory write through the API."""
    service = PostgresMemoryService(InMemorySemanticMemoryAdapter(), FakePolicyAdapter(allow=False))
    app.dependency_overrides[get_memory_service] = lambda: service
    try:
        response = TestClient(app).post("/brain/memory", json=memory_payload())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    body = response.json()
    assert body["error"]["code"] == "AION_FORBIDDEN"
    assert body["error"]["detail"]["reason"] == "denied"
