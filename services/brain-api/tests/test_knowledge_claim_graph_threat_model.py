from __future__ import annotations

from knowledge_source_registry_test_helpers import read_text

REQUIRED_THREATS = [
    "claim identity collision",
    "claim text injection",
    "raw prompt stored as claim",
    "hidden reasoning stored as claim",
    "user statement treated as fact",
    "engagement signal treated as fact",
    "malformed subject-predicate-object structure",
    "claim normalization collision",
    "source-registry reference spoofing",
    "citation spoofing",
    "provenance spoofing",
    "lineage-group spoofing",
    "evidence misbinding",
    "unsupported claim with no evidence",
    "duplicate evidence amplification",
    "mirror sources treated as independent",
    "source classification treated as truth",
    "jurisdiction mismatch",
    "version mismatch",
    "timezone ambiguity",
    "open-ended temporal interval ambiguity",
    "overlapping interval error",
    "non-overlapping historical claims treated as contradictory",
    "current claim superseding historical claim incorrectly",
    "correction relation tampering",
    "retraction relation tampering",
    "supersession cycles",
    "self-support relation",
    "self-contradiction relation",
    "relation-edge explosion",
    "graph query flooding",
    "graph fixture tampering",
    "persistent graph write",
    "graph-database creation",
    "claim verification bypass",
    "truth assignment bypass",
    "confidence assignment bypass",
    "knowledge-promotion bypass",
    "cognitive-belief mutation",
    "source-body leakage",
    "network acquisition",
    "background graph mutation",
    "authorization reuse",
    "evaluation evidence used as approval",
]


def test_claim_graph_threat_model_lists_required_threats_and_core_rule():
    text = read_text("docs/knowledge-intelligence/temporal-claim-evidence-graph-threat-model.md")
    for threat in REQUIRED_THREATS:
        assert threat in text
    assert "It does not decide truth" in text
    assert "Claim verification" in text
    assert "confidence assignment" in text
    assert "knowledge promotion" in text
    assert "cognitive-belief mutation" in text
