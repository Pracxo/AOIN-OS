"""Redaction helpers for AION-248."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.live_provider_pilot import (
    LiveProviderRedactionRecord,
    assert_no_protected_material,
)


def assert_redacted_evidence(payload: object) -> None:
    """Reject evidence containing raw content or credential material."""

    assert_no_protected_material(payload)


def create_redaction_record(
    *,
    redaction_id: str,
    request_projection_fingerprint: str,
    response_projection_fingerprint: str | None,
    created_at: datetime,
) -> LiveProviderRedactionRecord:
    """Create a redaction record."""

    return LiveProviderRedactionRecord(
        redaction_id=redaction_id,
        request_projection_fingerprint=request_projection_fingerprint,
        response_projection_fingerprint=response_projection_fingerprint,
        created_at=created_at,
    )
