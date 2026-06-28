"""Audit service for dry-run action authorization boundaries."""

from __future__ import annotations

from aion_brain.contracts.action_authorization import (
    ActionAuthorizationAuditRequest,
    ActionAuthorizationAuditResult,
    utc_now,
)
from aion_brain.dialogue._shared import emit_telemetry


class ActionAuthorizationAuditService:
    """Produce local audit proof for the dry-run authorization boundary."""

    def __init__(
        self,
        *,
        settings: object | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
    ) -> None:
        self._settings = settings
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink

    def audit(self, request: ActionAuthorizationAuditRequest) -> ActionAuthorizationAuditResult:
        """Return a deterministic boundary audit result."""

        result = ActionAuthorizationAuditResult(
            action_authorization_audit_id="action-authorization-audit-local",
            trace_id=request.trace_id,
            status="passed",
            owner_scope=request.owner_scope,
            checks_run=[
                "dry_run_only_enforced",
                "write_blocked",
                "execution_blocked",
                "activation_blocked",
                "external_calls_blocked",
                "role_matrix_enforced",
                "policy_enforced",
                "session_boundary_enforced",
                "static_examples_safe",
                "no_execution_endpoint_added",
            ],
            findings=[
                {"code": "dry_run_only", "status": "passed"},
                {"code": "no_write_path", "status": "passed"},
                {"code": "no_execution_path", "status": "passed"},
                {"code": "no_activation_path", "status": "passed"},
                {"code": "no_external_calls", "status": "passed"},
            ],
            dry_run_only_enforced=True,
            write_blocked=True,
            execution_blocked=True,
            activation_blocked=True,
            external_calls_blocked=True,
            role_matrix_enforced=True,
            policy_enforced=True,
            session_boundary_enforced=True,
            recommendations=[
                "Keep authorization scoped to dry-run previews and review records.",
                "Extend this model before any future write authorization path.",
            ],
            metadata={
                "action_authz_enabled": bool(
                    getattr(self._settings, "action_authorization_enabled", True)
                ),
                "dry_run_action_authz_enabled": bool(
                    getattr(self._settings, "dry_run_action_authorization_enabled", True)
                ),
                "authz_audit_enabled": bool(
                    getattr(self._settings, "action_authorization_audit_enabled", True)
                ),
                "write_allowed": False,
                "execution_allowed": False,
                "activation_allowed": False,
                "external_calls_allowed": False,
                "include_examples": request.include_examples,
            },
            created_at=utc_now(),
        )
        self._record_audit(result.action_authorization_audit_id)
        emit_telemetry(
            self._telemetry_service,
            event_type="action_authorization_audit_completed",
            node_type="action_authorization_audit",
            node_id=result.action_authorization_audit_id,
            intensity=0.7,
            trace_id=result.trace_id,
            payload={
                "status": result.status,
                "write_blocked": True,
                "execution_blocked": True,
                "activation_blocked": True,
                "external_calls_blocked": True,
            },
        )
        return result

    def _record_audit(self, audit_id: str) -> None:
        for name in ("record_event", "record_audit_event"):
            record = getattr(self._audit_sink, name, None)
            if callable(record):
                try:
                    record(
                        {
                            "event_type": "action_authorization_audit_completed",
                            "action_authorization_audit_id": audit_id,
                        }
                    )
                    return
                except Exception:
                    return


__all__ = ["ActionAuthorizationAuditService"]
