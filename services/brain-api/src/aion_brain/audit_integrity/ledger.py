"""Append-only tamper-evident audit ledger."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Protocol, cast
from uuid import uuid4

from aion_brain.audit_integrity.canonical import canonicalize_payload
from aion_brain.audit_integrity.hashing import hash_entry, hash_payload
from aion_brain.audit_integrity.redaction import redact_audit_payload
from aion_brain.audit_integrity.repository import AuditIntegrityRepository
from aion_brain.audit_integrity.status import build_audit_integrity_status
from aion_brain.config import Settings
from aion_brain.contracts.audit_integrity import (
    AuditEntry,
    AuditIntegrityStatus,
    AuditRecordRequest,
)
from aion_brain.contracts.telemetry import VisualTelemetryEvent


class AuditSink(Protocol):
    """Minimal audit sink protocol used by integrations."""

    def record(self, request: AuditRecordRequest) -> AuditEntry:
        """Append an audit record."""


class AuditIntegrityLedger:
    """Create append-only audit entries linked by sha256 hashes."""

    def __init__(
        self,
        audit_integrity_repository: AuditIntegrityRepository,
        policy_adapter: object | None,
        telemetry_service: object | None,
        settings: Settings,
    ) -> None:
        self._repository = audit_integrity_repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._settings = settings
        self._checkpoint_service: object | None = None

    def set_checkpoint_service(self, checkpoint_service: object | None) -> None:
        """Attach checkpoint service after kernel assembly."""
        self._checkpoint_service = checkpoint_service

    def record(self, request: AuditRecordRequest) -> AuditEntry:
        """Append one tamper-evident audit entry."""
        if not self._settings.audit_integrity_enabled:
            raise RuntimeError("audit_integrity_disabled")
        payload = request.payload if self._settings.audit_record_payloads else {}
        if self._settings.audit_redact_sensitive_payloads:
            redacted_payload, redaction_metadata = redact_audit_payload(payload)
        else:
            redacted_payload = payload
            redaction_metadata = {
                "redacted": False,
                "redaction_count": 0,
                "removed_count": 0,
                "field_paths": [],
                "removed_field_paths": [],
            }
        canonical_payload = canonicalize_payload(redacted_payload)
        payload_digest = hash_payload(canonical_payload)
        latest = self._repository.latest_entry()
        sequence_number = (latest.sequence_number if latest else 0) + 1
        previous_hash = latest.entry_hash if latest else None
        metadata = canonicalize_payload(request.metadata)
        entry_digest = hash_entry(previous_hash, payload_digest, sequence_number, metadata)
        entry = AuditEntry(
            audit_entry_id=request.audit_entry_id or f"audit-entry-{uuid4().hex}",
            sequence_number=sequence_number,
            trace_id=request.trace_id,
            correlation_id=request.correlation_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            action_type=request.action_type,
            resource_type=request.resource_type,
            resource_id=request.resource_id,
            event_type=request.event_type,
            outcome=request.outcome,
            risk_level=request.risk_level,
            policy_decision_id=request.policy_decision_id,
            autonomy_decision_id=request.autonomy_decision_id,
            risk_assessment_id=request.risk_assessment_id,
            approval_request_id=request.approval_request_id,
            command_id=request.command_id,
            source_component=request.source_component,
            payload_hash=payload_digest,
            previous_hash=previous_hash,
            entry_hash=entry_digest,
            hash_algorithm=self._settings.audit_hash_algorithm,
            canonical_payload=canonical_payload,
            redaction_metadata=redaction_metadata,
            metadata=metadata,
            created_at=datetime.now(UTC),
        )
        stored = self._repository.append_entry(entry)
        self._emit(
            "audit_entry_recorded",
            stored.audit_entry_id,
            stored.trace_id or stored.audit_entry_id,
            0.4,
            {"sequence_number": stored.sequence_number, "action_type": stored.action_type},
        )
        self._maybe_checkpoint(stored.sequence_number)
        return stored

    def get_entry(self, audit_entry_id: str) -> AuditEntry | None:
        """Return one audit entry."""
        return self._repository.get_entry(audit_entry_id)

    def get_by_sequence(self, sequence_number: int) -> AuditEntry | None:
        """Return one audit entry by sequence."""
        return self._repository.get_by_sequence(sequence_number)

    def list_entries(
        self,
        trace_id: str | None = None,
        resource_type: str | None = None,
        action_type: str | None = None,
        limit: int = 100,
    ) -> list[AuditEntry]:
        """List recent audit entries."""
        return self._repository.list_entries(
            trace_id=trace_id,
            resource_type=resource_type,
            action_type=action_type,
            limit=limit,
        )

    def status(self) -> AuditIntegrityStatus:
        """Return ledger integrity status."""
        return build_audit_integrity_status(self._repository)

    def _maybe_checkpoint(self, sequence_number: int) -> None:
        interval = self._settings.audit_checkpoint_interval
        if interval <= 0 or sequence_number % interval != 0:
            return
        create_checkpoint = getattr(self._checkpoint_service, "create_checkpoint", None)
        if not callable(create_checkpoint):
            return
        try:
            checkpoint = create_checkpoint()
            self._emit(
                "audit_checkpoint_created",
                checkpoint.checkpoint_id,
                checkpoint.checkpoint_id,
                0.6,
                {"to_sequence": checkpoint.to_sequence},
            )
        except Exception:
            return

    def _emit(
        self,
        event_type: str,
        node_id: str,
        trace_id: str,
        intensity: float,
        payload: dict[str, object],
    ) -> None:
        emit = getattr(self._telemetry_service, "emit", None)
        if not callable(emit):
            return
        try:
            emit(
                VisualTelemetryEvent(
                    telemetry_id=f"telemetry-{event_type}-{node_id}",
                    trace_id=trace_id,
                    event_type=event_type,  # type: ignore[arg-type]
                    node_type="audit",
                    node_id=node_id,
                    edge_from=trace_id,
                    edge_to=node_id,
                    intensity=intensity,
                    payload=payload,
                    created_at=datetime.now(UTC),
                )
            )
        except Exception:
            return


def record_audit_event(
    audit_sink: object | None,
    *,
    action_type: str,
    resource_type: str,
    event_type: str,
    outcome: str,
    source_component: str,
    payload: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    trace_id: str | None = None,
    correlation_id: str | None = None,
    actor_id: str | None = None,
    workspace_id: str | None = None,
    resource_id: str | None = None,
    risk_level: str | None = None,
    policy_decision_id: str | None = None,
    autonomy_decision_id: str | None = None,
    risk_assessment_id: str | None = None,
    approval_request_id: str | None = None,
    command_id: str | None = None,
) -> AuditEntry | None:
    """Best-effort integration helper that never hides the original result."""
    record = getattr(audit_sink, "record", None)
    if not callable(record):
        return None
    try:
        result = record(
            AuditRecordRequest(
                trace_id=trace_id,
                correlation_id=correlation_id,
                actor_id=actor_id,
                workspace_id=workspace_id,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                event_type=event_type,
                outcome=outcome,  # type: ignore[arg-type]
                risk_level=risk_level,
                policy_decision_id=policy_decision_id,
                autonomy_decision_id=autonomy_decision_id,
                risk_assessment_id=risk_assessment_id,
                approval_request_id=approval_request_id,
                command_id=command_id,
                source_component=source_component,
                payload=payload or {},
                metadata=metadata or {},
            )
        )
        return cast(AuditEntry, result)
    except Exception:
        return None


def record_local_auth_audit_event(
    audit_sink: object | None,
    *,
    audit_id: str,
    trace_id: str | None,
    actor_id: str | None,
    owner_scope: list[str],
    status: str,
) -> AuditEntry | None:
    """Record a local-auth safety audit without storing auth material."""
    return record_audit_event(
        audit_sink,
        action_type="local_auth.audit.run",
        resource_type="local_auth_audit",
        resource_id=audit_id,
        event_type="local_auth_audit_completed",
        outcome="completed" if status == "passed" else "failed",
        source_component="local_auth_audit_service",
        trace_id=trace_id,
        actor_id=actor_id,
        risk_level="medium",
        payload={
            "status": status,
            "owner_scope": owner_scope,
            "production_auth_enabled": False,
            "auth_material_enabled": False,
            "auth_session_state_enabled": False,
            "external_idp_enabled": False,
            "write_actions_enabled": False,
        },
        metadata={"dev_only": True},
    )


def record_local_session_audit_event(
    audit_sink: object | None,
    *,
    audit_id: str,
    trace_id: str | None,
    actor_id: str | None,
    owner_scope: list[str],
    status: str,
) -> AuditEntry | None:
    """Record a local-session safety audit without storing session material."""
    return record_audit_event(
        audit_sink,
        action_type="local_session.audit.run",
        resource_type="local_session_audit",
        resource_id=audit_id,
        event_type="local_session_audit_completed",
        outcome="completed" if status == "passed" else "failed",
        source_component="local_session_audit_service",
        trace_id=trace_id,
        actor_id=actor_id,
        risk_level="medium",
        payload={
            "status": status,
            "owner_scope": owner_scope,
            "dev_only": True,
            "read_only": True,
            "auth_material_enabled": False,
            "browser_state_enabled": False,
            "session_state_storage_enabled": False,
            "production_auth_enabled": False,
            "write_actions_enabled": False,
            "execution_enabled": False,
            "activation_enabled": False,
            "external_calls_enabled": False,
        },
        metadata={"local_only": True},
    )


def record_connector_runtime_audit(
    audit_sink: object | None,
    *,
    audit_id: str,
    trace_id: str | None,
    actor_id: str | None,
    owner_scope: list[str],
    status: str,
) -> AuditEntry | None:
    """Record a disabled connector-runtime audit without storing connector material."""
    return record_audit_event(
        audit_sink,
        action_type="connector_runtime.audit.run",
        resource_type="connector_runtime_audit",
        resource_id=audit_id,
        event_type="connector_runtime_audit_completed",
        outcome="completed" if status == "passed" else "failed",
        source_component="connector_runtime_audit_service",
        trace_id=trace_id,
        actor_id=actor_id,
        risk_level="medium",
        payload={
            "status": status,
            "owner_scope": owner_scope,
            "mock_only": True,
            "connector_runtime_enabled": False,
            "external_calls_enabled": False,
            "credentials_enabled": False,
            "token_storage_enabled": False,
            "activation_enabled": False,
            "route_registration_enabled": False,
        },
        metadata={"local_only": True, "read_only": True},
    )


def record_connector_simulator_audit(
    audit_sink: object | None,
    *,
    simulation_id: str,
    trace_id: str | None,
    actor_id: str | None,
    owner_scope: list[str],
    status: str,
) -> AuditEntry | None:
    """Record a synthetic connector simulation audit without connector material."""
    return record_audit_event(
        audit_sink,
        action_type="connector_simulator.simulate",
        resource_type="connector_simulation",
        resource_id=simulation_id,
        event_type="connector_simulation_completed",
        outcome="completed" if status in {"passed", "warning"} else "failed",
        source_component="connector_simulator",
        trace_id=trace_id,
        actor_id=actor_id,
        risk_level="medium",
        payload={
            "status": status,
            "owner_scope": owner_scope,
            "synthetic_only": True,
            "connector_runtime_enabled": False,
            "external_calls_made": False,
            "credentials_used": False,
            "tokens_used": False,
            "activation_allowed": False,
            "route_registration_allowed": False,
        },
        metadata={"local_only": True, "read_only": True},
    )


def record_connector_policy_audit(
    audit_sink: object | None,
    *,
    dry_run_id: str,
    trace_id: str | None,
    actor_id: str | None,
    owner_scope: list[str],
    status: str,
) -> AuditEntry | None:
    """Record a connector policy dry-run audit without connector material."""
    return record_audit_event(
        audit_sink,
        action_type="connector_policy.dry_run",
        resource_type="connector_policy_dry_run",
        resource_id=dry_run_id,
        event_type="connector_policy_dry_run_completed",
        outcome="completed" if status == "passed" else "failed",
        source_component="connector_policy",
        trace_id=trace_id,
        actor_id=actor_id,
        risk_level="medium",
        payload={
            "status": status,
            "owner_scope": owner_scope,
            "dry_run_only": True,
            "connector_runtime_enabled": False,
            "runtime_allowed": False,
            "external_call_allowed": False,
            "credential_access_allowed": False,
            "token_access_allowed": False,
            "activation_allowed": False,
            "route_registration_allowed": False,
        },
        metadata={"local_only": True, "read_only": True},
    )
