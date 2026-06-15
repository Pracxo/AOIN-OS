"""Backup redaction tests."""

from __future__ import annotations

from aion_brain.backups.redaction import (
    REDACTED,
    contains_sensitive_key,
    redact_record,
    strip_sensitive_metadata,
)


def test_redact_record_replaces_sensitive_values() -> None:
    record = {"id": "one", "payload": {"api_key": "secret", "value": "ok"}}

    redacted = redact_record(record, "redact_sensitive")

    assert redacted == {"id": "one", "payload": {"api_key": REDACTED, "value": "ok"}}


def test_exclude_sensitive_skips_restricted_or_secret_like_records() -> None:
    assert redact_record({"id": "one", "sensitivity": "restricted"}, "exclude_sensitive") is None
    assert redact_record({"id": "two", "token": "secret"}, "exclude_sensitive") is None


def test_metadata_only_keeps_only_identifying_fields() -> None:
    redacted = redact_record(
        {"event_id": "event-1", "payload": {"value": "hidden"}, "status": "ok"},
        "metadata_only",
    )

    assert redacted == {"event_id": "event-1", "status": "ok"}


def test_strip_sensitive_metadata_drops_secret_like_keys() -> None:
    assert contains_sensitive_key({"nested": {"private_key": "nope"}})
    assert strip_sensitive_metadata({"nested": {"private_key": "nope", "safe": True}}) == {
        "nested": {"safe": True}
    }
