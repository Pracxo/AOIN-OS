"""Evidence builders for persistent identity assertion replay protection."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from aion_brain.contracts.identity_assertion import normalize_utc_datetime
from aion_brain.contracts.identity_assertion_replay import (
    TABLE_NAME,
    IdentityAssertionReplayAuditEvent,
    IdentityAssertionReplayAuditEventType,
    IdentityAssertionReplayDiagnosticSnapshot,
    IdentityAssertionReplayPolicy,
    IdentityAssertionReplayProtectionBundle,
    IdentityAssertionReplayProtectionOutcome,
    IdentityAssertionReplayProtectionResult,
    IdentityAssertionReplayProvenanceRecord,
    IdentityAssertionReplayRepositoryResult,
)


def build_identity_assertion_replay_evidence_bundle(
    *,
    result: IdentityAssertionReplayProtectionResult,
    repository_result: IdentityAssertionReplayRepositoryResult | None,
    policy: IdentityAssertionReplayPolicy,
    created_at: datetime,
    bundle_id: str,
    event_id: str,
    provenance_id: str,
    snapshot_id: str,
    metadata: dict[str, Any] | None = None,
) -> IdentityAssertionReplayProtectionBundle:
    """Build correlated replay-protection evidence with redacted material only."""

    safe_metadata = metadata or {}
    event_type: IdentityAssertionReplayAuditEventType
    if result.outcome == "claimed":
        event_type = "identity_assertion_replay_claim_succeeded"
    elif result.outcome == "replay_detected":
        event_type = "identity_assertion_replay_detected"
    elif result.outcome == "identifier_collision":
        event_type = "identity_assertion_identifier_collision_detected"
    else:
        event_type = "identity_assertion_replay_failed_closed"
    normalized_created_at = normalize_utc_datetime(created_at)
    audit_event = IdentityAssertionReplayAuditEvent(
        event_id=event_id,
        event_type=event_type,
        replay_protection_id=result.replay_protection_id,
        replay_key=result.replay_key,
        issuer_fingerprint=result.issuer_fingerprint,
        assertion_fingerprint=result.assertion_fingerprint,
        outcome=result.outcome,
        claim_created=result.claim_created,
        replay_detected=result.replay_detected,
        identifier_collision=result.identifier_collision,
        repository_available=result.repository_available,
        schema_available=result.schema_available,
        retain_until=result.retain_until,
        reason_codes=result.reason_codes,
        created_at=normalized_created_at,
    )
    provenance = IdentityAssertionReplayProvenanceRecord(
        provenance_id=provenance_id,
        replay_protection_id=result.replay_protection_id,
        replay_key=result.replay_key,
        issuer_fingerprint=result.issuer_fingerprint,
        assertion_fingerprint=result.assertion_fingerprint,
        created_at=normalized_created_at,
        outcome=result.outcome,
        reason_codes=result.reason_codes,
    )
    diagnostic_snapshot = IdentityAssertionReplayDiagnosticSnapshot(
        snapshot_id=snapshot_id,
        replay_protection_id=result.replay_protection_id,
        table_name=TABLE_NAME,
        repository_available=result.repository_available,
        schema_available=result.schema_available,
        minimum_retention_seconds=policy.minimum_retention_seconds,
        maximum_retention_seconds=policy.maximum_retention_seconds,
        cleanup_batch_size=policy.cleanup_batch_size,
        allowed_clock_skew_seconds=policy.allowed_clock_skew_seconds,
        created_at=normalized_created_at,
    )
    return IdentityAssertionReplayProtectionBundle(
        bundle_id=bundle_id,
        replay_protection_id=result.replay_protection_id,
        result=result,
        repository_result=repository_result,
        audit_event=audit_event,
        provenance=provenance,
        diagnostic_snapshot=diagnostic_snapshot,
        verification_bundle_fingerprint=safe_metadata["verification_bundle_fingerprint"],
        created_at=normalized_created_at,
        metadata=safe_metadata,
    )


def replay_outcome_from_repository(
    repository_result: IdentityAssertionReplayRepositoryResult,
) -> IdentityAssertionReplayProtectionOutcome:
    """Map repository claim outcomes into protection outcomes."""

    return repository_result.outcome


__all__ = [
    "build_identity_assertion_replay_evidence_bundle",
    "replay_outcome_from_repository",
]
