from __future__ import annotations

from aion_brain.contracts.knowledge_source_registry import (
    SourceRegistryResourceBudget,
    SourceRegistryResourceUsage,
    evaluate_source_registry_budget,
)


def test_source_registry_budget_accepts_authorized_zero_write_projection_limits():
    decision = evaluate_source_registry_budget(
        SourceRegistryResourceUsage(
            registry_record_count=100,
            largest_record_envelope_bytes=8192,
            largest_metadata_bytes_per_record=4096,
            maximum_lineage_references_per_record=20,
            maximum_citation_references_per_record=20,
        )
    )
    assert decision.within_budget is True
    assert SourceRegistryResourceBudget().maximum_registry_write_batch == 0


def test_source_registry_budget_rejects_persistent_write_and_forbidden_counters():
    blocked_fields = {
        "registry_record_count": 101,
        "largest_record_envelope_bytes": 8193,
        "largest_metadata_bytes_per_record": 4097,
        "maximum_lineage_references_per_record": 21,
        "maximum_citation_references_per_record": 21,
        "persistent_write_batch": 1,
        "persisted_source_body_bytes": 1,
        "repository_source_body_bytes": 1,
        "claim_verifications": 1,
        "knowledge_promotions": 1,
        "belief_mutations": 1,
        "network_calls": 1,
        "git_operations": 1,
    }
    for field, value in blocked_fields.items():
        decision = evaluate_source_registry_budget(
            SourceRegistryResourceUsage.model_validate({field: value})
        )
        assert decision.within_budget is False, field
        assert decision.persistent_write_allowed is False
