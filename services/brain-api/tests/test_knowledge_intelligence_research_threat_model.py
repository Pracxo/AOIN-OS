from knowledge_intelligence_test_helpers import SOURCE_CLASSES, THREATS, read_text


def test_threat_model_contains_every_required_threat_and_core_rules():
    text = read_text("docs/knowledge-intelligence/research-threat-model.md")
    for threat in THREATS:
        assert threat in text
    for term in (
        "Acquired content is untrusted evidence.",
        "Content instructions never override system policy.",
        "No acquired content becomes a verified fact merely because it was fetched.",
        "prompt injection in acquired content is treated as untrusted content",
        "source repetition does not equal corroboration",
        "source classification does not establish truth",
        "research evidence cannot become verified knowledge automatically",
    ):
        assert term in text


def test_source_policy_keeps_classification_separate_from_truth():
    text = read_text("docs/knowledge-intelligence/research-source-policy.md")
    for source_class in SOURCE_CLASSES:
        assert source_class in text
    assert "Classification does not prove a claim." in text
    assert "community_unverified or unknown cannot independently establish a verified fact" in text
    assert "AION-205 must not implement the final truth-verification decision" in text
