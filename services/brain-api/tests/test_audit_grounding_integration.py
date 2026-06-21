from __future__ import annotations

from aion_brain.contracts.grounding import (
    GroundingSourceCreateRequest,
    GroundingVerificationRequest,
)
from tests.grounding_helpers import service_bundle


def test_grounding_records_audit_and_provenance_links() -> None:
    bundle = service_bundle()
    source = bundle.source_service.create_source(
        GroundingSourceCreateRequest(
            source_type="evidence",
            source_id="evidence-1",
            title="Evidence",
            summary="AION records deterministic source support.",
            trust_level="primary",
            owner_scope=["workspace:main"],
        )
    )

    citation_map = bundle.mapper.map_text(
        text="AION records deterministic source support.",
        trace_id="trace-1",
        owner_scope=["workspace:main"],
        sources=[source],
        target_type="response",
        target_id="response-1",
    )
    run = bundle.verifier.verify(
        GroundingVerificationRequest(
            response_id="response-1",
            target_type="response",
            owner_scope=["workspace:main"],
            text="AION records deterministic source support.",
        )
    )

    action_types = [entry.request.action_type for entry in bundle.audit.records]
    assert "grounding.source.create" in action_types
    assert "grounding.citation.create" in action_types
    assert "grounding.map" in action_types
    assert "grounding.coverage.read" in action_types
    assert "grounding.verify" in action_types

    links = {
        (link.source_type, link.source_id, link.target_type, link.target_id)
        for link in bundle.provenance.links
    }
    assert ("response", "response-1", "citation_map", citation_map.citation_map_id) in links
    assert (
        "grounding_verification",
        run.grounding_verification_id,
        "citation_map",
        run.result["citation_map_id"],
    ) in links
    assert any(
        link.source_type == "citation" and link.target_type == "grounding_source"
        for link in bundle.provenance.links
    )
