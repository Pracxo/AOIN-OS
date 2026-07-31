from secure_runtime_aion232_test_helpers import REPO_ROOT


def test_model_gateway_threat_model_records_required_threats_and_core_rule() -> None:
    text = (REPO_ROOT / "docs/secure-runtime-integration/model-gateway-threat-model.md").read_text()
    for phrase in (
        "provider spoofing",
        "model-ID substitution",
        "prompt injection",
        "secret exfiltration",
        "credential leakage",
        "token-budget evasion",
        "retry storms",
        "schema escape",
        "tool-call smuggling",
        "function-call smuggling",
        "model output treated as truth",
        "model output written to memory",
        "source rewrite",
        "Git mutation",
        "deployment",
        "model training",
    ):
        assert phrase in text
    assert "may not call a live provider under AION-232-SRI-0002" in text
