from __future__ import annotations

import pytest
from knowledge_research_test_helpers import NOW
from pydantic import ValidationError

from aion_brain.contracts.knowledge_research import CitationReference


def test_citation_reference_is_evidence_not_claim_verification():
    citation = CitationReference(
        citation_id="citation-reference-0001",
        snapshot_id="source-snapshot-0001",
        content_sha256="a" * 64,
        canonical_url_fingerprint="b" * 64,
        locator_kind="full_source",
        locator_value="full_source_metadata_only",
        retrieval_timestamp=NOW,
        citation_fingerprint="c" * 64,
    )
    assert citation.claim_verified is False
    with pytest.raises(ValidationError):
        CitationReference.model_validate({**citation.model_dump(), "claim_verified": True})
    with pytest.raises(ValidationError):
        CitationReference.model_validate({**citation.model_dump(), "locator_value": "raw prompt"})
