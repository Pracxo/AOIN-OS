"""Retrieval Router evidence source tests."""

from datetime import UTC, datetime

from aion_brain.contracts.evidence import EvidenceChunk, EvidenceRecord, EvidenceSearchResult
from aion_brain.retrieval.router import RetrievalRouter
from tests.test_retrieval_router import FakePolicyAdapter, make_request


class FakeEvidenceService:
    """Evidence search fake."""

    def search(self, request: object) -> list[EvidenceSearchResult]:
        return [
            EvidenceSearchResult(
                evidence=EvidenceRecord(
                    evidence_id="evidence-1",
                    trace_id="trace-1",
                    source_type="text",
                    source_ref=None,
                    owner_scope=["workspace:main"],
                    title="Alpha Evidence",
                    summary="alpha source",
                    content_hash="hash",
                    content_ref="evidence://evidence-1",
                    media_type="text/plain",
                    sensitivity="internal",
                    confidence=0.9,
                    metadata={},
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                    deleted_at=None,
                ),
                chunk=EvidenceChunk(
                    chunk_id="chunk-1",
                    evidence_id="evidence-1",
                    chunk_index=0,
                    text="alpha beta source",
                    text_hash="chunk-hash",
                    token_count_hint=3,
                    metadata={},
                    created_at=datetime.now(UTC),
                    deleted_at=None,
                ),
                score=0.8,
                matched_terms=["alpha"],
                metadata={},
            )
        ]


def test_retrieval_router_can_include_evidence_vault_results() -> None:
    """Evidence Vault search becomes retrieved context."""
    router = RetrievalRouter(
        policy_adapter=FakePolicyAdapter(),
        evidence_service=FakeEvidenceService(),
    )

    result = router.retrieve(make_request(["evidence_vault"]))

    assert result.items[0].source == "evidence_vault"
    assert result.items[0].evidence_ref == "evidence-1"
    assert result.items[0].metadata["chunk_id"] == "chunk-1"

