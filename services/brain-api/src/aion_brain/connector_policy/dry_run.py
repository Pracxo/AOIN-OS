"""Connector policy dry-run gate."""

from __future__ import annotations

from uuid import uuid4

from aion_brain.connector_policy.catalog import ConnectorPolicyCatalogService
from aion_brain.connector_policy.denials import ConnectorPolicyDenialService
from aion_brain.connector_policy.matrix import ConnectorAuthorizationMatrixService
from aion_brain.contracts.connector_policy import (
    ConnectorPolicyDecision,
    ConnectorPolicyDryRunRequest,
    ConnectorPolicyDryRunResult,
    utc_now,
)
from aion_brain.dialogue._shared import emit_telemetry


class ConnectorPolicyDryRunService:
    """Evaluate connector action requests without executing any connector behavior."""

    def __init__(
        self,
        *,
        catalog_service: ConnectorPolicyCatalogService,
        matrix_service: ConnectorAuthorizationMatrixService,
        denial_service: ConnectorPolicyDenialService,
        audit_service: object | None = None,
        settings: object | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._catalog_service = catalog_service
        self._matrix_service = matrix_service
        self._denial_service = denial_service
        self._audit_service = audit_service
        self._settings = settings
        self._telemetry_service = telemetry_service

    def evaluate(self, request: ConnectorPolicyDryRunRequest) -> ConnectorPolicyDryRunResult:
        """Return a dry-run decision with all runtime permissions denied."""

        action = self._catalog_service.get(request.requested_action_key)
        matrix = self._matrix_service.find(
            role=request.role,
            action_key=request.requested_action_key,
        )
        denial = self._denial_service.denial_for(request.requested_action_key)
        dry_run_enabled = bool(
            getattr(self._settings, "connector_policy_dry_run_enabled", True)
        )
        blockers = _runtime_blockers()
        warnings = [{"code": "connector_policy_dry_run_is_not_execution", "status": "open"}]
        decision: ConnectorPolicyDecision = "deny"
        dry_run_allowed = False
        review_required = True
        if denial is not None:
            blockers.append(
                {
                    "blocker_key": "explicit_denial_rule",
                    "action_key": request.requested_action_key,
                }
            )
        elif action is None:
            blockers.append({"blocker_key": "unknown_connector_policy_action"})
        elif not dry_run_enabled:
            blockers.append({"blocker_key": "connector_policy_dry_run_disabled"})
        elif matrix is None:
            blockers.append({"blocker_key": "missing_authorization_matrix_entry"})
        elif matrix.dry_run_allowed:
            decision = matrix.decision
            dry_run_allowed = True
            review_required = matrix.review_required
        else:
            blockers.append({"blocker_key": "role_denied_for_connector_policy_action"})

        result = ConnectorPolicyDryRunResult(
            connector_policy_dry_run_id=f"connector-policy-dry-run-{uuid4().hex}",
            trace_id=request.trace_id,
            connector_key=request.connector_key,
            requested_action_key=request.requested_action_key,
            role=request.role,
            decision=decision,
            dry_run_allowed=dry_run_allowed,
            runtime_allowed=False,
            external_call_allowed=False,
            credential_access_allowed=False,
            token_access_allowed=False,
            activation_allowed=False,
            review_required=review_required,
            audit_required=True,
            provenance_required=True,
            blockers=blockers,
            warnings=warnings,
            recommendations=[
                "keep_connector_runtime_disabled",
                "require_operator_review_before_future_runtime_work",
            ],
            metadata={
                "owner_scope": request.owner_scope,
                "declared_scopes": request.declared_scopes,
                "evidence_refs": request.evidence_refs,
                "runtime_allowed": False,
                "external_call_allowed": False,
                "credential_access_allowed": False,
                "token_access_allowed": False,
                "activation_allowed": False,
            },
            created_at=utc_now(),
        )
        record_dry_run = getattr(self._audit_service, "record_dry_run", None)
        if callable(record_dry_run):
            record_dry_run(
                dry_run_id=result.connector_policy_dry_run_id,
                trace_id=result.trace_id,
                actor_id=request.created_by,
                owner_scope=request.owner_scope,
                status="passed" if result.dry_run_allowed else "blocked",
            )
        emit_telemetry(
            self._telemetry_service,
            event_type="connector_policy_dry_run_completed",
            node_type="connector_policy_dry_run",
            node_id=result.connector_policy_dry_run_id,
            intensity=0.75 if not result.dry_run_allowed else 0.55,
            trace_id=result.trace_id,
            payload={"decision": result.decision, "runtime_allowed": False},
        )
        return result


def _runtime_blockers() -> list[dict[str, object]]:
    return [
        {"blocker_key": "connector_runtime_disabled", "bypassable": False},
        {"blocker_key": "external_calls_disabled", "bypassable": False},
        {"blocker_key": "credentials_tokens_disabled", "bypassable": False},
        {"blocker_key": "activation_disabled", "bypassable": False},
        {"blocker_key": "route_registration_disabled", "bypassable": False},
        {"blocker_key": "tool_write_execution_disabled", "bypassable": False},
    ]


__all__ = ["ConnectorPolicyDryRunService"]
