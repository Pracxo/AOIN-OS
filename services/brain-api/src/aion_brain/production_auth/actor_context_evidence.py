"""Builders for redacted actor-context resolution evidence."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from uuid import uuid4

from aion_brain.contracts.actor_context_resolution import (
    ActorContextResolutionAuditEvent,
    ActorContextResolutionBundle,
    ActorContextResolutionDiagnosticSnapshot,
    ActorContextResolutionInput,
    ActorContextResolutionProvenanceRecord,
    ActorContextResolutionReasonCode,
    ActorContextResolutionSource,
    ActorContextResolutionStatus,
    utc_now,
)
from aion_brain.contracts.scopes import ActorContext


def build_actor_context_resolution_bundle(
    *,
    resolution_input: ActorContextResolutionInput,
    actor_context: ActorContext,
    source: ActorContextResolutionSource,
    reason_codes: tuple[ActorContextResolutionReasonCode, ...],
    resolution_failed: bool = False,
    failure_reason: str | None = None,
    clock: Callable[[], datetime] = utc_now,
    id_factory: Callable[[str], str] | None = None,
) -> ActorContextResolutionBundle:
    """Build a deterministic, redacted actor-context resolution bundle."""

    ids = id_factory or (lambda prefix: f"{prefix}-{uuid4().hex}")
    created_at = clock()
    status = build_actor_context_resolution_status(
        resolution_input=resolution_input,
        actor_context=actor_context,
        source=source,
        reason_codes=reason_codes,
        clock=lambda: created_at,
        id_factory=ids,
    )
    audit_event = build_actor_context_resolution_audit_event(
        resolution_input=resolution_input,
        source=source,
        reason_codes=reason_codes,
        resolution_failed=resolution_failed,
        clock=lambda: created_at,
        id_factory=ids,
    )
    provenance = build_actor_context_resolution_provenance(
        resolution_input=resolution_input,
        source=source,
        clock=lambda: created_at,
        id_factory=ids,
    )
    diagnostic_snapshot = build_actor_context_resolution_diagnostic_snapshot(
        development_simulation_active=resolution_input.development_simulation_enabled,
        clock=lambda: created_at,
        id_factory=ids,
    )
    return ActorContextResolutionBundle(
        bundle_id=ids("actor-context-resolution-bundle"),
        request_id=resolution_input.request_id,
        trace_id=actor_context.trace_id,
        correlation_id=actor_context.correlation_id,
        source=source,
        actor_context=actor_context,
        status=status,
        audit_event=audit_event,
        provenance=provenance,
        diagnostic_snapshot=diagnostic_snapshot,
        reason_codes=reason_codes,
        resolution_failed=resolution_failed,
        failure_reason=failure_reason,
        created_at=created_at,
        metadata={
            "safe_correlation_only": True,
            "identity_header_values_stored": False,
            "request_context_identity_metadata_ignored": True,
        },
    )


def build_actor_context_resolution_status(
    *,
    resolution_input: ActorContextResolutionInput,
    actor_context: ActorContext,
    source: ActorContextResolutionSource,
    reason_codes: tuple[ActorContextResolutionReasonCode, ...],
    clock: Callable[[], datetime] = utc_now,
    id_factory: Callable[[str], str] | None = None,
) -> ActorContextResolutionStatus:
    """Build redacted resolution status."""

    ids = id_factory or (lambda prefix: f"{prefix}-{uuid4().hex}")
    return ActorContextResolutionStatus(
        status_id=ids("actor-context-resolution-status"),
        source=source,
        reason_codes=reason_codes,
        request_id_present=resolution_input.request_id is not None,
        trace_id_present=actor_context.trace_id is not None,
        correlation_id_present=actor_context.correlation_id is not None,
        request_identity_context_present=resolution_input.request_identity_context_present,
        request_identity_context_valid=resolution_input.request_identity_context_valid,
        development_identity_simulation_active=(
            resolution_input.development_simulation_enabled
        ),
        actor_id_present=actor_context.actor_id is not None,
        workspace_id_present=actor_context.workspace_id is not None,
        role_count=len(actor_context.roles),
        permission_count=len(actor_context.permissions),
        security_scope_count=len(actor_context.security_scope),
        dev_mode=actor_context.dev_mode,
        created_at=clock(),
        metadata={
            "development_value_count": _development_value_count(resolution_input),
            "request_context_actor_ignored": True,
            "request_context_workspace_ignored": True,
        },
    )


def build_actor_context_resolution_audit_event(
    *,
    resolution_input: ActorContextResolutionInput,
    source: ActorContextResolutionSource,
    reason_codes: tuple[ActorContextResolutionReasonCode, ...],
    resolution_failed: bool,
    clock: Callable[[], datetime] = utc_now,
    id_factory: Callable[[str], str] | None = None,
) -> ActorContextResolutionAuditEvent:
    """Build a redacted resolution audit event."""

    ids = id_factory or (lambda prefix: f"{prefix}-{uuid4().hex}")
    return ActorContextResolutionAuditEvent(
        event_id=ids("actor-context-resolution-audit"),
        event_type=(
            "actor_context_resolution_failed_closed"
            if resolution_failed
            else "actor_context_resolution_succeeded"
        ),
        request_id=resolution_input.request_id,
        trace_id=resolution_input.trace_id,
        correlation_id=resolution_input.correlation_id,
        source=source,
        reason_codes=reason_codes,
        development_header_value_count=(
            _development_value_count(resolution_input)
            if resolution_input.development_simulation_enabled
            else 0
        ),
        production_identity_header_values_stored=False,
        actor_context_failed_closed=resolution_failed,
        created_at=clock(),
        metadata={"header_value_redaction": "counts_only"},
    )


def build_actor_context_resolution_provenance(
    *,
    resolution_input: ActorContextResolutionInput,
    source: ActorContextResolutionSource,
    clock: Callable[[], datetime] = utc_now,
    id_factory: Callable[[str], str] | None = None,
) -> ActorContextResolutionProvenanceRecord:
    """Build redacted resolver provenance."""

    ids = id_factory or (lambda prefix: f"{prefix}-{uuid4().hex}")
    return ActorContextResolutionProvenanceRecord(
        provenance_id=ids("actor-context-resolution-provenance"),
        request_id=resolution_input.request_id,
        trace_id=resolution_input.trace_id,
        correlation_id=resolution_input.correlation_id,
        source=source,
        created_at=clock(),
        metadata={
            "core_input": "structured_safe_primitives",
            "request_context_projected_fields": ("trace_id", "correlation_id"),
        },
    )


def build_actor_context_resolution_diagnostic_snapshot(
    *,
    development_simulation_active: bool,
    clock: Callable[[], datetime] = utc_now,
    id_factory: Callable[[str], str] | None = None,
) -> ActorContextResolutionDiagnosticSnapshot:
    """Build safe process-level actor-context diagnostics."""

    ids = id_factory or (lambda prefix: f"{prefix}-{uuid4().hex}")
    return ActorContextResolutionDiagnosticSnapshot(
        diagnostic_id=ids("actor-context-resolution-diagnostic"),
        development_identity_simulation_active=development_simulation_active,
        created_at=clock(),
        metadata={"diagnostic_scope": "process_safe_state_only"},
    )


def _development_value_count(resolution_input: ActorContextResolutionInput) -> int:
    count = 0
    count += int(resolution_input.development_actor_id is not None)
    count += int(resolution_input.development_workspace_id is not None)
    count += len(resolution_input.development_roles)
    count += len(resolution_input.development_permissions)
    count += len(resolution_input.development_security_scope)
    return count


__all__ = [
    "build_actor_context_resolution_audit_event",
    "build_actor_context_resolution_bundle",
    "build_actor_context_resolution_diagnostic_snapshot",
    "build_actor_context_resolution_provenance",
    "build_actor_context_resolution_status",
]
