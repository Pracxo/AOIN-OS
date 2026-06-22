from __future__ import annotations

from aion_brain.contracts.citations import CitationCreateRequest
from tests.grounding_helpers import service_bundle, source


def test_source_coverage_recommends_avoid_memory_only_claim() -> None:
    bundle = service_bundle()
    memory_source = source().model_copy(
        update={
            "grounding_source_id": "memory-source-1",
            "source_type": "memory",
            "source_id": "memory-1",
            "trust_level": "memory_recall",
            "evidence_refs": [],
            "memory_refs": ["memory-1"],
        }
    )
    bundle.repository.save_source(memory_source)
    citation = bundle.citation_service.create_citation(
        CitationCreateRequest(
            response_id="response-1",
            source_type="memory",
            source_id="memory-1",
            grounding_source_id="memory-source-1",
            label="Memory",
            confidence=0.5,
            metadata={"owner_scope": ["workspace:main"]},
        )
    )

    report = bundle.coverage.report("response-1", None, ["workspace:main"], [])

    assert citation.citation_id
    assert "avoid_memory_only_claim" in report.recommendations
