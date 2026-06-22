"""Module activation redaction tests."""

from aion_brain.module_activation.redaction import redact_activation_payload


def test_activation_redaction_removes_secret_like_fields() -> None:
    payload = redact_activation_payload(
        {
            "token": "secret",
            "nested": {"raw_prompt": "hidden reasoning"},
            "safe": "value",
        }
    )

    assert payload["token"] == "[redacted]"
    assert payload["nested"]["raw_prompt"] == "[redacted]"
    assert payload["safe"] == "value"
