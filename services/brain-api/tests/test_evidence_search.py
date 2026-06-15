"""Evidence search tests."""

from aion_brain.contracts.evidence import EvidenceSearchRequest
from tests.test_evidence_service import FakeEvidenceRepository, make_ingest_request, make_service


def test_evidence_search_returns_lexical_matches() -> None:
    """Evidence search returns lexical matches."""
    service = make_service()
    service.ingest(make_ingest_request(content_text="alpha beta source text"))

    results = service.search(EvidenceSearchRequest(query="alpha", scope=["workspace:main"]))

    assert results
    assert results[0].evidence.evidence_id == "evidence-1"
    assert "alpha" in results[0].matched_terms


def test_evidence_search_respects_scope() -> None:
    """Evidence search filters by owner scope."""
    service = make_service()
    service.ingest(make_ingest_request(owner_scope=["workspace:main"]))

    results = service.search(EvidenceSearchRequest(query="alpha", scope=["workspace:other"]))

    assert results == []


def test_evidence_search_respects_source_type_filter() -> None:
    """Evidence search filters by source type."""
    service = make_service()
    service.ingest(make_ingest_request(source_type="system_note", content_text="alpha note"))

    results = service.search(
        EvidenceSearchRequest(
            query="alpha",
            scope=["workspace:main"],
            source_types=["user_input"],
        )
    )

    assert results == []


def test_evidence_search_excludes_deleted_evidence() -> None:
    """Deleted evidence is excluded from search."""
    repository = FakeEvidenceRepository()
    service = make_service(repository=repository)
    service.ingest(make_ingest_request(content_text="alpha beta"))
    service.soft_delete("evidence-1", ["workspace:main"])

    results = service.search(EvidenceSearchRequest(query="alpha", scope=["workspace:main"]))

    assert results == []

