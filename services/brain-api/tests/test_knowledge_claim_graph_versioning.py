from __future__ import annotations

from test_knowledge_claim_graph_helpers import claim, text_object


def test_new_record_version_preserves_history_without_mutating_old_claim() -> None:
    original = claim("claim-0001", object_value=text_object("alpha"))
    corrected = claim("claim-0002", object_value=text_object("beta"))
    assert original.claim_record_fingerprint != corrected.claim_record_fingerprint
    assert original.unverified is True
    assert corrected.knowledge_promoted is False
