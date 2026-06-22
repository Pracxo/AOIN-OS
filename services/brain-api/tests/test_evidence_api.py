"""Evidence API tests."""

from fastapi.testclient import TestClient

from aion_brain.api.evidence import get_evidence_service, get_grounding_service
from aion_brain.contracts.scopes import ActorContext
from aion_brain.evidence.grounding import GroundingService
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.main import app
from tests.test_evidence_service import (
    FakeEvidenceRepository,
    FakePolicyAdapter,
    make_actor_context,
    make_ingest_request,
    make_link,
    make_service,
)


def test_evidence_api_endpoints_work() -> None:
    """Evidence API supports ingest, read, search, links, grounding, and delete."""
    repository = FakeEvidenceRepository()
    evidence_service = make_service(repository=repository)
    grounding_service = GroundingService(
        evidence_service=evidence_service,
        grounding_repository=repository,
        policy_adapter=FakePolicyAdapter(),
        actor_context=make_actor_context(),
    )
    app.dependency_overrides[get_evidence_service] = lambda: evidence_service
    app.dependency_overrides[get_grounding_service] = lambda: grounding_service
    app.dependency_overrides[get_actor_context] = lambda: ActorContext(
        actor_id="actor-1",
        workspace_id="workspace-1",
        roles=["owner"],
        permissions=["evidence.restricted.read"],
        security_scope=["workspace:main"],
        dev_mode=True,
    )
    try:
        client = TestClient(app)
        ingest = client.post(
            "/brain/evidence",
            json=make_ingest_request(content_text="alpha beta " * 120).model_dump(mode="json"),
        )
        fetched = client.get("/brain/evidence/evidence-1", params={"scope": "workspace:main"})
        chunks = client.get(
            "/brain/evidence/evidence-1/chunks",
            params={"scope": "workspace:main"},
        )
        search = client.post(
            "/brain/evidence/search",
            json={"query": "alpha", "scope": ["workspace:main"], "limit": 10},
        )
        link = client.post("/brain/evidence/links", json=make_link().model_dump(mode="json"))
        links = client.get(
            "/brain/evidence/evidence-1/links",
            params={"scope": "workspace:main"},
        )
        ground = client.post(
            "/brain/evidence/ground",
            json={
                "trace_id": "trace-1",
                "statements": [{"statement_id": "statement-1", "statement": "alpha beta"}],
                "scope": ["workspace:main"],
            },
        )
        deleted = client.delete(
            "/brain/evidence/evidence-1",
            params={"scope": "workspace:main"},
        )
    finally:
        app.dependency_overrides.clear()

    assert ingest.status_code == 200
    assert ingest.json()["chunk_count"] >= 1
    assert fetched.status_code == 200
    assert chunks.status_code == 200
    assert chunks.json()
    assert search.status_code == 200
    assert search.json()
    assert link.status_code == 200
    assert links.status_code == 200
    assert links.json()[0]["target_id"] == "memory-1"
    assert ground.status_code == 200
    assert ground.json()["claims"][0]["verification_status"] == "supported"
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True
