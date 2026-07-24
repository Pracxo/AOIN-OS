from __future__ import annotations

from knowledge_source_registry_test_helpers import ROOT, read_json, read_text


def test_claim_graph_boundary_documents_unverified_assertion_scope():
    text = read_text("docs/knowledge-intelligence/temporal-claim-evidence-graph-boundary.md")
    for phrase in (
        "explicit structured unverified claim assertions",
        "Source registry references are required",
        "citation binding is required",
        "Automatic claim extraction",
        "truth decision",
        "epistemic confidence",
        "persistent graph writes",
        "network acquisition",
    ):
        assert phrase in text


def test_claim_graph_examples_remain_unimplemented_and_unverified():
    assertion = read_json("examples/knowledge-intelligence/unverified-claim-assertion.json")
    binding = read_json("examples/knowledge-intelligence/claim-evidence-binding.json")
    edge = read_json("examples/knowledge-intelligence/claim-relation-edge.json")
    assertion_payload = assertion["payload"]
    binding_payload = binding["payload"]
    edge_payload = edge["payload"]
    assert assertion["temporal_claim_evidence_graph_implemented"] is True
    assert assertion_payload["unverified"] is True
    assert assertion_payload["verified"] is False
    assert assertion_payload["knowledge_promoted"] is False
    assert assertion_payload["belief_created"] is False
    assert binding_payload["source_registry_record_ids"]
    assert binding_payload["citation_record_ids"]
    assert binding_payload["verified_support"] is False
    assert edge_payload["relation_verified"] is False
    assert edge_payload["truth_effect"] is False
    assert edge_payload["knowledge_effect"] is False
    for relative in (
        "services/brain-api/src/aion_brain/contracts/knowledge_claim_graph.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph.py",
    ):
        assert (ROOT / relative).is_file(), relative
