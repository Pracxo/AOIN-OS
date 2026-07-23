from knowledge_source_registry_test_helpers import SOURCE_SCOPE, read_json, read_text


def test_source_registry_scope_documents_authorized_and_prohibited_surfaces():
    text = read_text("docs/knowledge-intelligence/source-provenance-registry-boundary.md")
    assert SOURCE_SCOPE in read_text(
        "docs/knowledge-intelligence/source-provenance-registry-architecture.md"
    )
    for term in (
        "append-only",
        "metadata",
        "Source content remains untrusted evidence",
        "source classification does not establish truth",
        "must not store full source bodies",
        "must not make any claim-verification decision",
    ):
        assert term in text
    payload = read_json("examples/knowledge-intelligence/source-registry-record-envelope.json")
    assert payload["source_body_present"] is False
    assert payload["source_body_bytes"] == 0
    assert payload["source_body_persistence_enabled"] is False
    assert payload["claim_verification_enabled"] is False
