"""Approval control-plane service."""

from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import uuid4

from aion_brain.approvals.repository import ApprovalRepository
from aion_brain.approvals.state_machine import require_valid_approval_transition
from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.config import Settings
from aion_brain.contracts.approvals import (
    ApprovalCreateRequest,
    ApprovalDecision,
    ApprovalDecisionRequest,
    ApprovalInboxQuery,
    ApprovalLifecycleEvent,
    ApprovalPriority,
    ApprovalRequest,
    ApprovalStatus,
)
from aion_brain.contracts.guardrails import (
    RiskGuardrailEvaluation,
    RiskGuardrailEvaluationRequest,
)
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.guardrails.engine import GuardrailEngine
from aion_brain.policy.base import PolicyAdapter
from aion_brain.risk.engine import RiskEngine


class ApprovalService:
    """Central approval service for risk, guardrail, and human decisions."""

    def __init__(
        self,
        *,
        repository: ApprovalRepository,
        risk_engine: RiskEngine,
        guardrail_engine: GuardrailEngine,
        policy_adapter: PolicyAdapter,
        telemetry_service: object | None,
        settings: Settings,
        audit_sink: object | None = None,
    ) -> None:
        self._repository = repository
        self._risk_engine = risk_engine
        self._guardrail_engine = guardrail_engine
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._settings = settings
        self._audit_sink = audit_sink

    def create_request(self, request: ApprovalCreateRequest) -> ApprovalRequest:
        """Create and persist a pending approval request."""
        decision = self._authorize(
            action_type="approval.request.create",
            resource_type=request.resource_type,
            resource_id=request.resource_id,
            risk_level="medium",
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            scope=request.approval_scope,
            approval_present=True,
            context=request.model_dump(mode="json"),
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")
        now = datetime.now(UTC)
        expires_at = request.expires_at or (
            now + timedelta(hours=self._settings.approval_default_expiry_hours)
        )
        approval = ApprovalRequest(
            approval_request_id=request.approval_request_id or f"approval-{uuid4().hex}",
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            requested_by=request.requested_by or request.actor_id,
            assigned_to=request.assigned_to,
            action_type=request.action_type,
            resource_type=request.resource_type,
            resource_id=request.resource_id,
            title=request.title,
            description=request.description,
            risk_assessment_id=request.risk_assessment_id,
            guardrail_decision_id=request.guardrail_decision_id,
            status="pending",
            priority=request.priority,
            approval_scope=request.approval_scope,
            payload=request.payload,
            constraints=request.constraints,
            expires_at=expires_at,
            created_at=now,
            updated_at=now,
            resolved_at=None,
        )
        saved = self._repository.save_request(approval)
        self._record_lifecycle(saved, "approval_created", None, "pending", request.actor_id)
        if saved.assigned_to:
            self._record_lifecycle(
                saved,
                "approval_assigned",
                "pending",
                "pending",
                saved.assigned_to,
            )
        self._emit(saved, "approval_created", 0.7)
        record_audit_event(
            self._audit_sink,
            action_type="approval.request",
            resource_type=saved.resource_type,
            resource_id=saved.resource_id or saved.approval_request_id,
            event_type="approval_created",
            outcome="waiting_for_approval",
            source_component="approval_service",
            trace_id=saved.trace_id,
            actor_id=saved.actor_id,
            workspace_id=saved.workspace_id,
            risk_assessment_id=saved.risk_assessment_id,
            approval_request_id=saved.approval_request_id,
            payload={
                "status": saved.status,
                "priority": saved.priority,
                "action_type": saved.action_type,
            },
        )
        return saved

    def get_request(self, approval_request_id: str, scope: list[str]) -> ApprovalRequest | None:
        """Return one approval request after policy authorization."""
        decision = self._authorize(
            action_type="approval.request.read",
            resource_type="approval_request",
            resource_id=approval_request_id,
            risk_level="low",
            trace_id=None,
            actor_id=None,
            workspace_id=None,
            scope=scope,
            approval_present=False,
            context={},
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")
        approval = self._repository.get_request(approval_request_id)
        if approval is None or not _scope_matches(approval.approval_scope, scope):
            return None
        return approval

    def list_pending(self, query: ApprovalInboxQuery) -> list[ApprovalRequest]:
        """Return approval inbox items."""
        decision = self._authorize(
            action_type="approval.request.read",
            resource_type="approval_request",
            resource_id=None,
            risk_level="low",
            trace_id=None,
            actor_id=query.actor_id,
            workspace_id=query.workspace_id,
            scope=query.scope,
            approval_present=False,
            context=query.model_dump(mode="json"),
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")
        return self._repository.list_requests(query)

    def decide(self, request: ApprovalDecisionRequest) -> ApprovalDecision:
        """Approve, deny, or cancel a pending approval request."""
        approval = self._repository.get_request(request.approval_request_id)
        if approval is None:
            raise ValueError("approval_request_not_found")
        target_status: ApprovalStatus = _status_for_decision(request.decision)
        require_valid_approval_transition(approval.status, target_status)
        decision = self._authorize(
            action_type=(
                "approval.request.cancel"
                if request.decision == "cancel"
                else "approval.decision.create"
            ),
            resource_type=approval.resource_type,
            resource_id=approval.resource_id,
            risk_level="medium",
            trace_id=approval.trace_id,
            actor_id=request.decided_by,
            workspace_id=approval.workspace_id,
            scope=approval.approval_scope,
            approval_present=True,
            context=request.model_dump(mode="json"),
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")
        now = datetime.now(UTC)
        record = ApprovalDecision(
            approval_decision_id=f"approval-decision-{uuid4().hex}",
            approval_request_id=request.approval_request_id,
            trace_id=approval.trace_id,
            decided_by=request.decided_by,
            decision=request.decision,
            reason=request.reason,
            decision_payload=request.decision_payload,
            created_at=now,
        )
        self._repository.save_decision(record)
        updated = approval.model_copy(
            update={
                "status": target_status,
                "updated_at": now,
                "resolved_at": now,
            }
        )
        self._repository.save_request(updated)
        event_type = _lifecycle_event_for_status(target_status)
        self._record_lifecycle(
            updated,
            event_type,
            approval.status,
            target_status,
            request.decided_by,
            request.reason,
            request.decision_payload,
        )
        self._emit(updated, event_type, 0.9 if target_status in {"denied", "cancelled"} else 1.0)
        record_audit_event(
            self._audit_sink,
            action_type="approval.decision",
            resource_type=updated.resource_type,
            resource_id=updated.resource_id or updated.approval_request_id,
            event_type=event_type,
            outcome="denied" if target_status == "denied" else "completed",
            source_component="approval_service",
            trace_id=updated.trace_id,
            actor_id=request.decided_by,
            workspace_id=updated.workspace_id,
            risk_assessment_id=updated.risk_assessment_id,
            approval_request_id=updated.approval_request_id,
            payload={"decision": request.decision, "status": updated.status},
        )
        return record

    def cancel(
        self,
        approval_request_id: str,
        *,
        actor_id: str | None,
        reason: str,
    ) -> ApprovalRequest:
        """Cancel one pending approval request."""
        self.decide(
            ApprovalDecisionRequest(
                approval_request_id=approval_request_id,
                decided_by=actor_id,
                decision="cancel",
                reason=reason,
                decision_payload={},
            )
        )
        approval = self._repository.get_request(approval_request_id)
        if approval is None:
            raise ValueError("approval_request_not_found")
        return approval

    def expire(self, approval_request_id: str) -> ApprovalRequest:
        """Expire one pending approval request."""
        approval = self._repository.get_request(approval_request_id)
        if approval is None:
            raise ValueError("approval_request_not_found")
        require_valid_approval_transition(approval.status, "expired")
        decision = self._authorize(
            action_type="approval.expire",
            resource_type=approval.resource_type,
            resource_id=approval.resource_id,
            risk_level="low",
            trace_id=approval.trace_id,
            actor_id=None,
            workspace_id=approval.workspace_id,
            scope=approval.approval_scope,
            approval_present=True,
            context={},
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")
        now = datetime.now(UTC)
        updated = approval.model_copy(
            update={"status": "expired", "updated_at": now, "resolved_at": now}
        )
        saved = self._repository.save_request(updated)
        self._record_lifecycle(saved, "approval_expired", approval.status, "expired", None)
        self._emit(saved, "approval_expired", 0.5)
        return saved

    def evaluate_and_maybe_request(
        self,
        request: RiskGuardrailEvaluationRequest,
    ) -> RiskGuardrailEvaluation:
        """Assess risk, evaluate guardrails, and create approval when required."""
        risk = self._risk_engine.assess(request.risk)
        guardrail = self._guardrail_engine.evaluate(
            risk.model_copy(update={"metadata": {**risk.metadata, **request.risk.context}})
        )
        final_decision = _final_decision(
            risk.decision,
            guardrail.blocked,
            guardrail.approval_required,
        )
        approval = None
        if final_decision == "require_approval" and self._settings.approvals_enabled:
            approval = self.create_request(
                ApprovalCreateRequest(
                    trace_id=risk.trace_id,
                    actor_id=risk.actor_id,
                    workspace_id=risk.workspace_id,
                    requested_by=risk.actor_id,
                    action_type=risk.action_type,
                    resource_type=risk.resource_type,
                    resource_id=risk.resource_id,
                    title=f"Approval required for {risk.action_type}",
                    description=(
                        "AION requires approval before continuing this generic action."
                    ),
                    risk_assessment_id=risk.risk_assessment_id,
                    guardrail_decision_id=guardrail.guardrail_decision_id,
                    priority=_priority_for_risk(risk.computed_risk_level),
                    approval_scope=_scope_from_request(request),
                    payload=_safe_payload(request.risk.payload),
                    constraints=[*risk.constraints, *guardrail.constraints],
                )
            )
        return RiskGuardrailEvaluation(
            risk_assessment=risk,
            guardrail_decision=guardrail,
            approval_request=approval,
            final_decision=cast(Any, final_decision),
            reason=_evaluation_reason(final_decision, risk.decision, guardrail.reason),
            created_at=datetime.now(UTC),
        )

    def _authorize(
        self,
        *,
        action_type: str,
        resource_type: str,
        resource_id: str | None,
        risk_level: str,
        trace_id: str | None,
        actor_id: str | None,
        workspace_id: str | None,
        scope: list[str],
        approval_present: bool,
        context: dict[str, Any],
    ) -> PolicyDecision:
        return self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{resource_id or uuid4().hex}",
                trace_id=trace_id,
                actor_id=actor_id,
                workspace_id=workspace_id,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                risk_level=risk_level,
                approval_present=approval_present,
                requested_permissions=[],
                security_scope=scope,
                context=context,
            )
        )

    def _record_lifecycle(
        self,
        approval: ApprovalRequest,
        event_type: str,
        from_status: str | None,
        to_status: str | None,
        actor_id: str | None,
        reason: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> ApprovalLifecycleEvent:
        event = ApprovalLifecycleEvent(
            approval_event_id=f"approval-event-{uuid4().hex}",
            approval_request_id=approval.approval_request_id,
            trace_id=approval.trace_id,
            event_type=cast(Any, event_type),
            from_status=from_status,
            to_status=to_status,
            actor_id=actor_id,
            reason=reason,
            payload=payload or {},
            created_at=datetime.now(UTC),
        )
        return self._repository.save_lifecycle_event(event)

    def _emit(self, approval: ApprovalRequest, event_type: str, intensity: float) -> None:
        if self._telemetry_service is None:
            return
        event = VisualTelemetryEvent(
            telemetry_id=f"telemetry-{approval.approval_request_id}-{event_type}",
            trace_id=approval.trace_id or approval.approval_request_id,
            event_type=cast(Any, event_type),
            node_type="approval",
            node_id=approval.approval_request_id,
            edge_from=approval.guardrail_decision_id or approval.risk_assessment_id,
            edge_to=approval.approval_request_id,
            intensity=intensity,
            payload={
                "status": approval.status,
                "action_type": approval.action_type,
                "resource_type": approval.resource_type,
                "owner_scope": approval.approval_scope,
            },
            created_at=datetime.now(UTC),
        )
        try:
            emit = getattr(self._telemetry_service, "emit", None)
            if callable(emit):
                emit(event)
                return
            save = getattr(self._telemetry_service, "save_visual_telemetry", None)
            if callable(save):
                save(event.trace_id, [event])
        except Exception:
            return


def _status_for_decision(decision: str) -> ApprovalStatus:
    if decision == "approve":
        return "approved"
    if decision == "deny":
        return "denied"
    return "cancelled"


def _lifecycle_event_for_status(status: ApprovalStatus) -> str:
    if status == "approved":
        return "approval_approved"
    if status == "denied":
        return "approval_denied"
    if status == "cancelled":
        return "approval_cancelled"
    return "approval_expired"


def _final_decision(
    risk_decision: str,
    guardrail_blocked: bool,
    guardrail_approval_required: bool,
) -> str:
    if guardrail_blocked or risk_decision == "block":
        return "block"
    if guardrail_approval_required or risk_decision == "require_approval":
        return "require_approval"
    return "allow"


def _evaluation_reason(final_decision: str, risk_decision: str, guardrail_reason: str) -> str:
    if final_decision == "block":
        return guardrail_reason if guardrail_reason != "no_guardrail_matched" else "risk_blocked"
    if final_decision == "require_approval":
        return "approval_required"
    return "allowed"


def _priority_for_risk(risk_level: str) -> ApprovalPriority:
    if risk_level == "critical":
        return "urgent"
    if risk_level == "high":
        return "high"
    return "normal"


def _scope_from_request(request: RiskGuardrailEvaluationRequest) -> list[str]:
    value = request.risk.context.get("security_scope") or request.risk.metadata.get(
        "security_scope"
    )
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    if request.risk.workspace_id:
        return [f"workspace:{request.risk.workspace_id}"]
    return ["workspace:main"]


def _safe_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if "secret" not in str(key).lower()}


def _scope_matches(approval_scope: list[str], query_scope: list[str]) -> bool:
    return bool(set(approval_scope) & set(query_scope))
