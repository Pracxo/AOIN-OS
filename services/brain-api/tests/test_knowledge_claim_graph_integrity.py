from __future__ import annotations

from test_knowledge_claim_graph_helpers import graph_batch

from aion_brain.knowledge_intelligence.claim_graph_integrity import (
    audit_temporal_claim_evidence_graph,
)


def test_integrity_audit_passes_valid_graph_and_reports_redacted_findings() -> None:
    service, registry, _claims, batch = graph_batch()
    repository, _decision = service.simulate_append(
        __import__(
            "aion_brain.knowledge_intelligence.claim_graph_repository",
            fromlist=["InMemoryTemporalClaimGraphRepository"],
        ).InMemoryTemporalClaimGraphRepository(),
        batch,
    )
    report = service.audit(repository, source_registry_repository=registry)
    assert report.status.value == "passed"
    broken = batch.records[1].model_copy(update={"previous_record_fingerprint": None})
    bad_report = audit_temporal_claim_evidence_graph((batch.records[0], broken))
    assert bad_report.status.value == "failed"
    assert "Claim graph integrity invariant failed." in bad_report.findings[0].redacted_summary
    assert "alpha" not in bad_report.findings[0].redacted_summary.lower()
