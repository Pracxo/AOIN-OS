from __future__ import annotations

from test_knowledge_claim_graph_helpers import evidence_binding


def test_source_independence_groups_are_metadata_only() -> None:
    binding = evidence_binding()
    assert binding.lineage_group_ids == ("independence-group-0001",)
    assert binding.verified_support is False
    assert binding.truth_effect is False
    assert binding.confidence_effect is False
