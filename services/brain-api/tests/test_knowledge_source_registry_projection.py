from __future__ import annotations

from knowledge_source_registry_implementation_helpers import NOW, valid_batch, valid_evidence_bundle

from aion_brain.knowledge_intelligence.source_registry import (
    project_research_evidence_bundle,
)


def test_source_registry_projection_creates_deterministic_metadata_records_only():
    bundle = valid_evidence_bundle()
    batch = project_research_evidence_bundle(bundle, clock=lambda: NOW)
    assert [record.record_kind for record in batch.records] == [
        "source_snapshot_digest",
        "source_provenance",
        "citation_reference",
        "source_lineage",
        "deduplication_decision",
        "operator_review_reference",
    ]
    assert [record.sequence_number for record in batch.records] == [1, 2, 3, 4, 5, 6]
    rendered = batch.model_dump_json().lower()
    assert "https://research.example.invalid" not in rendered
    assert "redacted_preview" not in rendered
    assert "content_artifact_id" not in rendered
    assert "content-type" not in rendered
    assert "official_standard" in rendered


def test_source_registry_projection_preserves_disabled_truth_knowledge_and_belief_state():
    batch = valid_batch()
    for record in batch.records:
        assert record.claim_verified is False
        assert record.knowledge_promoted is False
        assert record.belief_created is False
        payload = record.payload.model_dump(mode="json")
        assert payload.get("verified_fact") is not True
        assert payload.get("source_claims_verified") is not True
        assert payload.get("claim_verified") is not True
        assert payload.get("knowledge_promoted") is not True
        assert payload.get("belief_created") is not True
