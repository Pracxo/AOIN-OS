from __future__ import annotations

import pytest
from knowledge_research_test_helpers import NOW
from pydantic import ValidationError

from aion_brain.knowledge_intelligence.source_provenance import SourceProvenanceRecord


def test_source_provenance_records_declared_metadata_without_truth_conclusion():
    record = SourceProvenanceRecord(
        provenance_id="source-provenance-0001",
        snapshot_id="source-snapshot-0001",
        canonical_url_fingerprint="a" * 64,
        content_sha256="b" * 64,
        source_class="official_standard",
        declared_author=None,
        declared_publisher="Synthetic Standards Body",
        declared_title="Synthetic Standard",
        declared_publication_timestamp=None,
        declared_modification_timestamp=None,
        retrieval_timestamp=NOW,
        metadata_sources=("transport_headers",),
        robots_policy_status="allowed",
        licence_policy_status="permitted",
        redirect_chain_fingerprint="c" * 64,
        destination_validation_fingerprint="d" * 64,
        safe_headers_fingerprint="e" * 64,
        adapter_type="in_memory",
        provenance_fingerprint="f" * 64,
    )
    assert record.source_claims_verified is False
    with pytest.raises(ValidationError):
        SourceProvenanceRecord.model_validate(
            {**record.model_dump(), "declared_title": "contains raw prompt"}
        )
