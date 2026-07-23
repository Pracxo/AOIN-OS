from knowledge_source_registry_test_helpers import read_text


def test_source_registry_threat_model_contains_required_controls():
    text = read_text("docs/knowledge-intelligence/source-provenance-registry-threat-model.md")
    for term in (
        "source body leakage",
        "digest spoofing",
        "citation spoofing",
        "lineage tampering",
        "source classification being mistaken for truth",
        "prompt injection in source metadata",
        "registry overwrite attempts",
        "unauthorized runtime writes",
        "migration drift",
        "API route drift",
        "Git mutation",
        "knowledge promotion bypass",
        "append-only records",
        "zero source body persistence",
        "no live network requests",
        "no claim verification",
        "no knowledge promotion",
        "no belief mutation",
        "no runtime activation",
        "no privileged bypass",
    ):
        assert term in text
