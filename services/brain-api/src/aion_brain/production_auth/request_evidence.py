"""Evidence builders for disabled request identity boundaries."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from aion_brain.contracts.request_identity import (
    AUTHORIZATION_TRANSACTION_ID,
    BOUNDARY_VERSION,
    IMPLEMENTATION_TASK,
    REQUIRED_REASON_CODES,
    RequestIdentityAuditEvent,
    RequestIdentityAuditEventType,
    RequestIdentityBoundaryStatus,
    RequestIdentityContext,
    RequestIdentityDiagnosticSnapshot,
    RequestIdentityProvenanceRecord,
    RequestIdentityVerificationResult,
    RequestIdentityVerifierType,
    utc_now,
)


def build_request_identity_context(
    verification: RequestIdentityVerificationResult,
    *,
    clock: Callable[[], datetime] = utc_now,
    id_factory: Callable[[str], str],
) -> RequestIdentityContext:
    """Build an immutable anonymous disabled request identity context."""

    return RequestIdentityContext(
        context_id=id_factory("request-identity-context"),
        verification_id=verification.verification_id,
        request_id=verification.request_id,
        trace_id=verification.trace_id,
        correlation_id=verification.correlation_id,
        identity_source=verification.identity_source,
        reason_codes=tuple(REQUIRED_REASON_CODES),
        created_at=clock(),
        metadata={"source": "disabled_verification_result"},
    )


def build_request_identity_audit_event(
    *,
    event_type: RequestIdentityAuditEventType,
    verification: RequestIdentityVerificationResult,
    context: RequestIdentityContext | None,
    clock: Callable[[], datetime] = utc_now,
    id_factory: Callable[[str], str],
    metadata: dict[str, object] | None = None,
) -> RequestIdentityAuditEvent:
    """Build a redacted request identity audit event."""

    return RequestIdentityAuditEvent(
        event_id=id_factory("request-identity-audit"),
        event_type=event_type,
        request_id=verification.request_id,
        trace_id=verification.trace_id,
        correlation_id=verification.correlation_id,
        context_id=context.context_id if context is not None else None,
        verification_id=verification.verification_id,
        identity_source=verification.identity_source,
        reason_codes=tuple(REQUIRED_REASON_CODES),
        created_at=clock(),
        metadata=metadata or {"event_scope": "request_identity_boundary"},
    )


def build_request_identity_provenance_record(
    *,
    verification: RequestIdentityVerificationResult,
    verifier_type: RequestIdentityVerifierType,
    clock: Callable[[], datetime] = utc_now,
    id_factory: Callable[[str], str],
    metadata: dict[str, object] | None = None,
) -> RequestIdentityProvenanceRecord:
    """Build redacted request identity provenance references."""

    source_refs = [
        f"authorization_transaction:{AUTHORIZATION_TRANSACTION_ID}",
        f"implementation_task:{IMPLEMENTATION_TASK}",
        f"request_id:{verification.request_id}",
        f"boundary_version:{BOUNDARY_VERSION}",
        f"verifier_type:{verifier_type}",
    ]
    if verification.trace_id:
        source_refs.append(f"trace_id:{verification.trace_id}")
    if verification.correlation_id:
        source_refs.append(f"correlation_id:{verification.correlation_id}")
    return RequestIdentityProvenanceRecord(
        provenance_id=id_factory("request-identity-provenance"),
        request_id=verification.request_id,
        trace_id=verification.trace_id,
        correlation_id=verification.correlation_id,
        source_refs=tuple(source_refs),
        verifier_type=verifier_type,
        identity_source=verification.identity_source,
        reason_codes=tuple(REQUIRED_REASON_CODES),
        created_at=clock(),
        metadata=metadata or {"evidence_kind": "disabled_request_identity_boundary"},
    )


def build_request_identity_status(
    *,
    registered: bool = False,
    clock: Callable[[], datetime] = utc_now,
    id_factory: Callable[[str], str],
    metadata: dict[str, object] | None = None,
) -> RequestIdentityBoundaryStatus:
    """Build safe boundary status."""

    return RequestIdentityBoundaryStatus(
        status_id=id_factory("request-identity-status"),
        request_identity_boundary_registered=registered,
        reason_codes=tuple(REQUIRED_REASON_CODES),
        created_at=clock(),
        metadata=metadata or {"runtime_surface": "absent"},
    )


def build_request_identity_diagnostic_snapshot(
    *,
    registered: bool = False,
    verifier_type: RequestIdentityVerifierType = "disabled",
    clock: Callable[[], datetime] = utc_now,
    id_factory: Callable[[str], str],
    metadata: dict[str, object] | None = None,
) -> RequestIdentityDiagnosticSnapshot:
    """Build safe process diagnostics for the request identity boundary."""

    return RequestIdentityDiagnosticSnapshot(
        snapshot_id=id_factory("request-identity-diagnostic"),
        request_identity_boundary_registered=registered,
        verifier_type=verifier_type,
        reason_codes=tuple(REQUIRED_REASON_CODES),
        blocker_count=len(REQUIRED_REASON_CODES),
        created_at=clock(),
        metadata=metadata or {"diagnostics": "redacted"},
    )


__all__ = [
    "build_request_identity_audit_event",
    "build_request_identity_context",
    "build_request_identity_diagnostic_snapshot",
    "build_request_identity_provenance_record",
    "build_request_identity_status",
]
