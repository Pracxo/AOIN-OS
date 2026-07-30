from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.secure_runtime import (
    SecureRuntimeAuditRecord,
    reject_secure_runtime_protected_material,
)
from tests.secure_runtime_test_support import NOW


def test_redaction_rejects_raw_signature_and_prompt_material() -> None:
    with pytest.raises(ValueError):
        reject_secure_runtime_protected_material({"signature": "abc"})
    with pytest.raises(ValueError):
        reject_secure_runtime_protected_material({"nested": {"raw_prompt": "hidden"}})


def test_audit_metadata_never_accepts_credentials_or_tokens() -> None:
    with pytest.raises(ValidationError):
        SecureRuntimeAuditRecord(
            audit_record_id="audit-AION-231",
            session_id="session-AION-231",
            event_type="identity_verification_passed",
            prior_audit_hash="0" * 64,
            metadata={"token": "secret"},
            created_at=NOW,
        )
