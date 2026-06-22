"""Retrieval API tests."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.api.retrieval import (
    get_context_fusion_engine,
    get_retrieval_repository,
    get_retrieval_router,
)
from aion_brain.contracts.retrieval import (
    ContextBundle,
    ContextFusionRequest,
    RetrievalRequest,
    RetrievalResult,
    RetrievedContextItem,
)
from aion_brain.main import app


class FakeRetrievalRouter:
    """Router fake for API tests."""

    def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        return make_result(request.retrieval_id)


class FakeFusionEngine:
    """Fusion fake for API tests."""

    def fuse(self, request: ContextFusionRequest) -> ContextBundle:
        return ContextBundle(
            bundle_id="bundle-1",
            retrieval_id=request.retrieval_result.retrieval_id,
            goal=request.goal,
            items=request.retrieval_result.items,
            fused_summary="Retrieved context for goal: alpha",
            memory_refs=["memory-1"],
            capability_refs=[],
            graph_node_refs=[],
            graph_edge_refs=[],
            trace_refs=[],
            constraints=[],
            token_budget_hint=100,
            created_at=datetime.now(UTC),
        )


class FakeRetrievalRepository:
    """Retrieval repository fake for API tests."""

    def get(self, retrieval_id: str) -> RetrievalResult | None:
        if retrieval_id == "missing":
            return None
        return make_result(retrieval_id)


def test_retrieval_query_api_returns_retrieval_result() -> None:
    """POST /brain/retrieval/query returns RetrievalResult."""
    app.dependency_overrides[get_retrieval_router] = lambda: FakeRetrievalRouter()
    try:
        response = TestClient(app).post("/brain/retrieval/query", json=request_payload())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["retrieval_id"] == "retrieval-1"


def test_retrieval_fuse_api_returns_context_bundle() -> None:
    """POST /brain/retrieval/fuse returns ContextBundle."""
    result = make_result("retrieval-1").model_dump(mode="json")
    app.dependency_overrides[get_context_fusion_engine] = lambda: FakeFusionEngine()
    try:
        response = TestClient(app).post(
            "/brain/retrieval/fuse",
            json={"retrieval_result": result, "goal": "alpha"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["bundle_id"] == "bundle-1"


def test_get_retrieval_api_returns_persisted_result() -> None:
    """GET /brain/retrieval/{retrieval_id} returns persisted retrieval."""
    app.dependency_overrides[get_retrieval_repository] = lambda: FakeRetrievalRepository()
    try:
        response = TestClient(app).get("/brain/retrieval/retrieval-1")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["retrieval_id"] == "retrieval-1"


def request_payload() -> dict[str, object]:
    """Create a retrieval request payload."""
    return {
        "retrieval_id": "retrieval-1",
        "trace_id": "trace-1",
        "intent_id": "intent-1",
        "query": "alpha",
        "scope": ["workspace:main"],
        "requested_sources": ["lexical_memory"],
        "limit": 10,
    }


def make_result(retrieval_id: str) -> RetrievalResult:
    """Create a retrieval result."""
    return RetrievalResult(
        retrieval_id=retrieval_id,
        query="alpha",
        items=[
            RetrievedContextItem(
                item_id="item-1",
                source="lexical_memory",
                source_id="memory-1",
                title="semantic",
                content="alpha beta",
                score=0.8,
                confidence=0.9,
                sensitivity="low",
                owner_scope=["workspace:main"],
                memory_type="semantic",
                capability_id=None,
                graph_node_ids=[],
                graph_edge_ids=[],
                trace_refs=[],
                evidence_ref=None,
                metadata={},
            )
        ],
        source_counts={"lexical_memory": 1},
        constraints=[],
        created_at=datetime.now(UTC),
    )
