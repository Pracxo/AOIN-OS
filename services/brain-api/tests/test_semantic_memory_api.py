"""Semantic memory API tests."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.api.memory import get_semantic_memory_service
from aion_brain.contracts.memory import (
    MemoryRecord,
    SemanticAdapterStatus,
    SemanticIndexResponse,
    SemanticMemoryQuery,
    SemanticMemoryResult,
    TurboVecIndexStatus,
    TurboVecRebuildRequest,
    TurboVecRebuildResponse,
)
from aion_brain.main import app


class FakeSemanticService:
    """Fake semantic service for API tests."""

    def reindex(self, memory_id: str, scope: list[str]) -> SemanticIndexResponse:
        return SemanticIndexResponse(
            indexed=True,
            memory_id=memory_id,
            adapter_name="fake",
            embedding_id=f"fake-{memory_id}",
            reason=None,
        )

    def retrieve(self, query: SemanticMemoryQuery) -> list[SemanticMemoryResult]:
        return [
            SemanticMemoryResult(
                memory=memory_record(),
                score=0.8,
                retrieval_source="semantic",
                adapter_name="fake",
                matched_terms=["alpha"],
                metadata={},
            )
        ]

    def adapter_statuses(self, scope: list[str]) -> list[SemanticAdapterStatus]:
        return [
            SemanticAdapterStatus(
                adapter_name="turbovec",
                active=True,
                available=True,
                default=True,
                reason=None,
                metadata={"scope": scope},
            )
        ]

    def turbovec_status(
        self,
        index_name: str = "default",
        scope: list[str] | None = None,
    ) -> TurboVecIndexStatus:
        return turbovec_status(index_name=index_name)

    def rebuild_turbovec(self, request: TurboVecRebuildRequest) -> TurboVecRebuildResponse:
        return TurboVecRebuildResponse(
            rebuilt=not request.dry_run,
            dry_run=request.dry_run,
            index_name=request.index_name,
            indexed=2,
            skipped=0,
            failed=0,
            status=turbovec_status(index_name=request.index_name),
            reason=None,
        )

    def reindex_turbovec(
        self,
        memory_id: str,
        *,
        index_name: str,
        force: bool,
        scope: list[str],
    ) -> SemanticIndexResponse:
        return SemanticIndexResponse(
            indexed=True,
            memory_id=memory_id,
            adapter_name="turbovec",
            embedding_id=f"turbovec-{index_name}-{memory_id}",
            reason=None,
        )


def test_semantic_index_api_returns_expected_shape() -> None:
    """Semantic index endpoint returns SemanticIndexResponse."""
    app.dependency_overrides[get_semantic_memory_service] = lambda: FakeSemanticService()
    try:
        response = TestClient(app).post("/brain/memory/semantic/index/memory-1")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "indexed": True,
        "memory_id": "memory-1",
        "adapter_name": "fake",
        "embedding_id": "fake-memory-1",
        "reason": None,
    }


def test_semantic_retrieve_api_returns_results() -> None:
    """Semantic retrieve endpoint returns SemanticMemoryResult contracts."""
    app.dependency_overrides[get_semantic_memory_service] = lambda: FakeSemanticService()
    try:
        response = TestClient(app).post(
            "/brain/memory/semantic/retrieve",
            json={"query": "alpha", "scope": ["workspace:main"], "limit": 10},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["memory"]["memory_id"] == "memory-1"
    assert response.json()[0]["adapter_name"] == "fake"


def test_semantic_adapters_api_returns_public_statuses() -> None:
    """Semantic adapter listing returns public status contracts."""
    app.dependency_overrides[get_semantic_memory_service] = lambda: FakeSemanticService()
    try:
        response = TestClient(app).get("/brain/memory/semantic/adapters")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["adapter_name"] == "turbovec"
    assert response.json()[0]["available"] is True


def test_turbovec_status_api_returns_public_status() -> None:
    """TurboVec status endpoint does not expose vendor objects."""
    app.dependency_overrides[get_semantic_memory_service] = lambda: FakeSemanticService()
    try:
        response = TestClient(app).get(
            "/brain/memory/semantic/turbovec/status?index_name=default"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["adapter_name"] == "turbovec"
    assert response.json()["available"] is True


def test_turbovec_rebuild_api_returns_counts() -> None:
    """TurboVec rebuild endpoint returns deterministic rebuild metadata."""
    app.dependency_overrides[get_semantic_memory_service] = lambda: FakeSemanticService()
    try:
        response = TestClient(app).post(
            "/brain/memory/semantic/turbovec/rebuild",
            json={"scope": ["workspace:main"], "dry_run": True, "limit": 10},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["dry_run"] is True
    assert response.json()["indexed"] == 2


def test_turbovec_reindex_api_returns_index_response() -> None:
    """TurboVec single-memory reindex endpoint returns SemanticIndexResponse."""
    app.dependency_overrides[get_semantic_memory_service] = lambda: FakeSemanticService()
    try:
        response = TestClient(app).post(
            "/brain/memory/semantic/turbovec/reindex/memory-1",
            json={"index_name": "default", "force": True},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["adapter_name"] == "turbovec"
    assert response.json()["embedding_id"] == "turbovec-default-memory-1"


def memory_record() -> MemoryRecord:
    """Create a memory record."""
    return MemoryRecord(
        memory_id="memory-1",
        memory_type="semantic",
        owner_scope=["workspace:main"],
        source_event_id=None,
        content_ref=None,
        summary="alpha beta",
        confidence=0.9,
        sensitivity="low",
        created_at=datetime.now(UTC),
        expires_at=None,
        metadata={},
    )


def turbovec_status(index_name: str = "default") -> TurboVecIndexStatus:
    """Create a TurboVec status contract."""
    now = datetime.now(UTC)
    return TurboVecIndexStatus(
        index_id=f"turbovec-{index_name}",
        index_name=index_name,
        adapter_name="turbovec",
        dimensions=384,
        bit_width=4,
        index_path=f"/tmp/{index_name}.tvindex",
        status="active",
        entry_count=2,
        available=True,
        reason=None,
        metadata={},
        created_at=now,
        updated_at=now,
        rebuilt_at=None,
    )
