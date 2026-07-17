"""Evidence builders for offline identity assertion verification."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from aion_brain.contracts.identity_assertion import (
    MANDATORY_RUNTIME_BOUNDARY_REASON_CODES,
    SUCCESS_REASON_CODES,
    IdentityAssertionAuditEvent,
    IdentityAssertionAuditEventType,
    IdentityAssertionDiagnosticSnapshot,
    IdentityAssertionEnvelope,
    IdentityAssertionProvenanceRecord,
    IdentityAssertionReasonCode,
    IdentityAssertionVerificationBundle,
    IdentityAssertionVerificationPolicy,
    IdentityAssertionVerificationResult,
    assertion_fingerprint,
    claim_counts_for_payload,
    normalize_utc_datetime,
    validate_reason_codes,
)


def success_reason_codes() -> tuple[IdentityAssertionReasonCode, ...]:
    """Return immutable success reason codes."""

    return tuple(SUCCESS_REASON_CODES)


def rejection_reason_codes(
    primary_reason_code: IdentityAssertionReasonCode,
) -> tuple[IdentityAssertionReasonCode, ...]:
    """Return immutable rejection reason codes with mandatory runtime boundary codes."""

    if primary_reason_code == "identity_assertion_verified":
        raise ValueError("rejection primary reason cannot be success")
    return validate_reason_codes(
        (
            "identity_assertion_rejected",
            primary_reason_code,
            *MANDATORY_RUNTIME_BOUNDARY_REASON_CODES,
        )
    )


def build_identity_assertion_verification_bundle(
    *,
    envelope: IdentityAssertionEnvelope | None,
    verified: bool,
    primary_reason_code: IdentityAssertionReasonCode,
    verified_at: datetime,
    verification_id: str,
    bundle_id: str,
    event_id: str,
    provenance_id: str,
    snapshot_id: str,
    public_key_count: int,
    policy: IdentityAssertionVerificationPolicy,
    metadata: dict[str, Any] | None = None,
) -> IdentityAssertionVerificationBundle:
    """Build redacted correlated verification evidence."""

    created_at = normalize_utc_datetime(verified_at)
    payload = envelope.payload if envelope is not None else None
    key_id = envelope.key_id if envelope is not None else None
    claim_counts = claim_counts_for_payload(payload)
    event_type: IdentityAssertionAuditEventType
    if verified:
        reason_codes = success_reason_codes()
        result_primary: IdentityAssertionReasonCode = "identity_assertion_verified"
        event_type = "identity_assertion_verification_succeeded"
    else:
        reason_codes = rejection_reason_codes(primary_reason_code)
        result_primary = primary_reason_code
        event_type = "identity_assertion_verification_rejected"
    safe_metadata = metadata or {}
    result = IdentityAssertionVerificationResult(
        verification_id=verification_id,
        assertion_id=payload.assertion_id if payload is not None else None,
        key_id=key_id,
        issuer=payload.issuer if payload is not None else None,
        audience=payload.audience if payload is not None else None,
        verified=verified,
        rejected=not verified,
        primary_reason_code=result_primary,
        reason_codes=reason_codes,
        claim_counts=claim_counts,
        assertion_fingerprint=assertion_fingerprint(payload),
        verified_at=created_at,
        metadata=safe_metadata,
    )
    audit_event = IdentityAssertionAuditEvent(
        event_id=event_id,
        event_type=event_type,
        verification_id=verification_id,
        assertion_id_present=payload is not None and bool(payload.assertion_id),
        key_id=key_id,
        issuer=payload.issuer if payload is not None else None,
        audience=payload.audience if payload is not None else None,
        verified=verified,
        rejected=not verified,
        reason_codes=reason_codes,
        claim_counts=claim_counts,
        created_at=created_at,
        metadata=safe_metadata,
    )
    provenance = IdentityAssertionProvenanceRecord(
        provenance_id=provenance_id,
        verification_id=verification_id,
        source_refs=(
            "AION-161-PA-0006",
            "docs/adr/0153-v02-offline-ed25519-identity-assertion-verification.md",
        ),
        public_key_registry_key_count=public_key_count,
        created_at=created_at,
        metadata=safe_metadata,
    )
    diagnostic_snapshot = IdentityAssertionDiagnosticSnapshot(
        snapshot_id=snapshot_id,
        trusted_public_key_count=public_key_count,
        allowed_clock_skew_seconds=policy.allowed_clock_skew_seconds,
        maximum_assertion_lifetime_seconds=policy.maximum_assertion_lifetime_seconds,
        created_at=created_at,
        metadata=safe_metadata,
    )
    return IdentityAssertionVerificationBundle(
        bundle_id=bundle_id,
        verification_id=verification_id,
        result=result,
        audit_event=audit_event,
        provenance=provenance,
        diagnostic_snapshot=diagnostic_snapshot,
        created_at=created_at,
        metadata=safe_metadata,
    )


__all__ = [
    "build_identity_assertion_verification_bundle",
    "rejection_reason_codes",
    "success_reason_codes",
]
