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
    assert assertion["unverified"] is True
    assert assertion["verified"] is False
    assert assertion["knowledge_promoted"] is False
    assert assertion["belief_created"] is False
    assert binding["source_registry_record_ids"]
    assert binding["citation_ids"]
    assert binding["verified_support"] is False
    assert edge["structural_conflict_candidate"] is True
    assert edge["one_claim_true"] is False
    assert edge["one_claim_false"] is False
    for relative in (
        "services/brain-api/src/aion_brain/contracts/knowledge_claim_graph.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph.py",
    ):
        assert not (ROOT / relative).exists(), relative
