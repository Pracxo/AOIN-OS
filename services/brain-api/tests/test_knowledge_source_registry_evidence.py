from __future__ import annotations

from datetime import timedelta

import pytest
from knowledge_source_registry_implementation_helpers import NOW, valid_batch
from pydantic import ValidationError

from aion_brain.knowledge_intelligence.source_registry import (
    ControlledSourceProvenanceRegistry,
)
from aion_brain.knowledge_intelligence.source_registry_evidence import (
    SourceRegistryIncidentRecord,
    SourceRegistryOperatorReviewItem,
    build_source_registry_evidence_bundle,
)
from aion_brain.knowledge_intelligence.source_registry_repository import (
    InMemorySourceRegistryRepository,
)


def test_source_registry_evidence_contains_only_redacted_counts_and_fingerprints():
    batch = valid_batch()
    registry = ControlledSourceProvenanceRegistry(clock=lambda: NOW)
    repository, decision = registry.simulate_append(InMemorySourceRegistryRepository(), batch)
    report = registry.audit(repository)
    evidence = build_source_registry_evidence_bundle(
        record_kinds=tuple(record.record_kind for record in batch.records),
        source_classes=("official_standard",),
        integrity_report=report,
        budget_decision=batch.budget_decision,
        append_decision=decision,
        registry_batch_fingerprint=batch.batch_fingerprint,
        clock=lambda: NOW,
    )
    rendered = evidence.model_dump_json().lower()
    assert "synthetic evidence for operator review" not in rendered
    assert "https://research.example.invalid" not in rendered
    assert evidence.operator_review_items[0].approval_created is False
    assert evidence.operator_review_items[0].implementation_authorization_created is False


def test_source_registry_evidence_rejects_exception_text_and_unbounded_review_expiry():
    with pytest.raises(ValidationError):
        SourceRegistryIncidentRecord(
            incident_id="source-registry-incident-0001",
            severity="high",
            reason_codes=("source_registry_fixture_rejected",),
            redacted_summary="Traceback exception text",
            created_at=NOW,
            fingerprint="a" * 64,
        )
    with pytest.raises(ValidationError):
        SourceRegistryOperatorReviewItem(
            review_item_id="source-registry-review-bad",
            registry_batch_fingerprint="a" * 64,
            integrity_report_fingerprint="b" * 64,
            append_decision_fingerprint="c" * 64,
            created_at=NOW,
            expires_at=NOW + timedelta(days=8),
            fingerprint="d" * 64,
        )
