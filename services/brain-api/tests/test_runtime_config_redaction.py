"""Runtime config redaction tests."""

from __future__ import annotations

from aion_brain.runtime_config.redaction import redact_config_value, sanitize_config_dict


def test_redaction_redacts_secret_like_values() -> None:
    assert redact_config_value("api_key", "raw") == {"redacted": True}
    assert sanitize_config_dict({"nested": {"token": "raw"}}) == {
        "nested": {"token": {"redacted": True}}
    }
