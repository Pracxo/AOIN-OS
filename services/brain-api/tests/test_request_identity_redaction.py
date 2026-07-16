from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.request_identity import (
    RequestIdentityProvenanceRecord,
    RequestIdentityVerificationInput,
    RequestIdentityVerificationResult,
)

FIXED_NOW = datetime(2026, 7, 16, 10, 0, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    "metadata",
    [
        {"password": "redacted"},
        {"Credential": "redacted"},
        {"authorization-header": "redacted"},
        {"nested": {"access-token": "redacted"}},
        {"sessionToken": "redacted"},
        {"raw_claims": {"sub": "demo"}},
        {"note": "contains bearer token material"},
        {"note": "raw prompt should not appear"},
        {"ｐａｓｓｗｏｒｄ": "redacted"},
    ],
)
def test_request_identity_rejects_protected_metadata(metadata: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        RequestIdentityVerificationInput(request_id="request-1", metadata=metadata)


def test_request_identity_rejects_protected_source_refs() -> None:
    with pytest.raises(ValidationError):
        RequestIdentityProvenanceRecord(
            provenance_id="provenance-1",
            request_id="request-1",
            source_refs=("provider payload:demo",),
            created_at=FIXED_NOW,
        )


def test_request_identity_exception_text_is_sanitized_by_contract() -> None:
    with pytest.raises(ValidationError) as error:
        RequestIdentityVerificationResult(
            verification_id="verification-1",
            request_id="request-1",
            metadata={"client-secret": "raw"},
            created_at=FIXED_NOW,
        )

    assert "client-secret" not in str(error.value)
