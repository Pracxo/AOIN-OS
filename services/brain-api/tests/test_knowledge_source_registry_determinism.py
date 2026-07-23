from __future__ import annotations

from knowledge_source_registry_implementation_helpers import NOW, fixed_id, valid_evidence_bundle

from aion_brain.knowledge_intelligence.source_registry import project_research_evidence_bundle
from aion_brain.knowledge_intelligence.source_registry_index import build_source_registry_index
from aion_brain.knowledge_intelligence.source_registry_integrity import audit_source_registry


def test_source_registry_projection_index_and_audit_are_deterministic():
    bundle = valid_evidence_bundle()
    batch_one = project_research_evidence_bundle(bundle, clock=lambda: NOW, id_factory=fixed_id)
    batch_two = project_research_evidence_bundle(bundle, clock=lambda: NOW, id_factory=fixed_id)
    assert batch_one == batch_two
    assert build_source_registry_index(batch_one.records) == build_source_registry_index(
        batch_two.records
    )
    assert audit_source_registry(batch_one.records, clock=lambda: NOW) == audit_source_registry(
        batch_two.records,
        clock=lambda: NOW,
    )


def test_source_registry_fingerprints_change_when_source_provenance_or_citation_changes():
    batch_one = project_research_evidence_bundle(
        valid_evidence_bundle(b"body-one"),
        clock=lambda: NOW,
        id_factory=fixed_id,
    )
    batch_two = project_research_evidence_bundle(
        valid_evidence_bundle(b"body-two"),
        clock=lambda: NOW,
        id_factory=fixed_id,
    )
    assert batch_one.batch_fingerprint != batch_two.batch_fingerprint
    assert batch_one.records[0].record_fingerprint != batch_two.records[0].record_fingerprint
    assert batch_one.records[1].record_fingerprint != batch_two.records[1].record_fingerprint
    assert batch_one.records[2].record_fingerprint != batch_two.records[2].record_fingerprint
