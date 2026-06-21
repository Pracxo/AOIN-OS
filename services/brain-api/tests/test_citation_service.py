from __future__ import annotations

from aion_brain.contracts.citations import CitationCreateRequest
from tests.grounding_helpers import service_bundle


def test_citation_service_creates_and_lists_citation() -> None:
    bundle = service_bundle()

    citation = bundle.citation_service.create_citation(
        CitationCreateRequest(
            response_id="response-1",
            source_type="evidence",
            source_id="evidence-1",
            citation_type="supports_statement",
            label="Evidence",
            quote="AION records deterministic support.",
            confidence=0.8,
            verified=True,
            metadata={"owner_scope": ["workspace:main"]},
        )
    )

    citations = bundle.citation_service.list_citations(response_id="response-1")
    deleted = bundle.citation_service.soft_delete_citation(citation.citation_id, None, "test")

    assert citations[0].citation_id == citation.citation_id
    assert deleted is True
