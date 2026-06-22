"""Policy-gated memory forgetting workflow."""

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.config import Settings
from aion_brain.contracts.approvals import ApprovalCreateRequest
from aion_brain.contracts.autonomy import AutonomyDecisionRequest
from aion_brain.contracts.memory import MemoryRecord
from aion_brain.contracts.memory_governance import (
    ForgetMemoryRequest,
    ForgetMemoryResult,
    MemoryForgettingRequestRecord,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.risk import RiskAssessment, RiskAssessmentRequest, RiskLevel
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.memory_governance.repository import MemoryGovernanceRepository
from aion_brain.policy.base import PolicyAdapter


class MemoryForgettingService:
    """Forget memory-owned targets without hard deletes."""

    def __init__(
        self,
        *,
        memory_service: object | None,
        semantic_memory_service: object | None,
        graph_memory_service: object | None,
        evidence_service: object | None,
        skill_service: object | None,
        trace_repository: object | None,
        risk_engine: object | None,
        approval_service: object | None,
        policy_adapter: PolicyAdapter,
        governance_repository: MemoryGovernanceRepository,
        telemetry_service: object | None,
        settings: Settings,
        autonomy_governor: object | None = None,
    ) -> None:
        self._memory_service = memory_service
        self._semantic_memory_service = semantic_memory_service
        self._graph_memory_service = graph_memory_service
        self._evidence_service = evidence_service
        self._skill_service = skill_service
        self._trace_repository = trace_repository
        self._risk_engine = risk_engine
        self._approval_service = approval_service
        self._policy_adapter = policy_adapter
        self._repository = governance_repository
        self._telemetry_service = telemetry_service
        self._settings = settings
        self._autonomy_governor = autonomy_governor

    def forget(self, request: ForgetMemoryRequest) -> ForgetMemoryResult:
        """Run a policy-gated soft-forget request."""
        forget_id = request.forget_request_id or f"forget-{uuid4().hex}"
        policy = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"memory.forget.request-{forget_id}",
                trace_id=request.trace_id,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                action_type="memory.forget.request",
                resource_type=request.target_type,
                resource_id=request.target_id,
                risk_level=_risk_for_target(request.target_type),
                approval_present=request.approval_present,
                requested_permissions=[],
                security_scope=request.owner_scope,
                context=request.model_dump(mode="json"),
            )
        )
        if not policy.allow:
            result = _result(
                request,
                forget_id,
                status="blocked_by_policy",
                forgotten=False,
                approval_required=False,
                approval_request_id=None,
                affected=[],
                preserved=[],
                reason=policy.reason,
                resolved_at=datetime.now(UTC),
            )
            self._save_request(request, result, None, None)
            self._emit_forget(result, "memory_forget_blocked", 0.9)
            return result

        risk = self._assess_risk(request)
        if self._settings.memory_forgetting_requires_approval and not request.approval_present:
            approval_id = self._create_approval(request, risk, forget_id)
            result = _result(
                request,
                forget_id,
                status="pending_approval",
                forgotten=False,
                approval_required=True,
                approval_request_id=approval_id,
                affected=[],
                preserved=_preserved_refs(self._memory_service, request),
                reason="approval_required",
                resolved_at=None,
            )
            self._save_request(request, result, risk, approval_id)
            self._emit_forget(result, "memory_forget_requested", 0.8)
            return result

        autonomy = self._autonomy_decision(request)
        if autonomy is not None and not bool(getattr(autonomy, "allow", False)):
            result = _result(
                request,
                forget_id,
                status="blocked_by_policy",
                forgotten=False,
                approval_required=False,
                approval_request_id=None,
                affected=[],
                preserved=_preserved_refs(self._memory_service, request),
                reason=str(getattr(autonomy, "reason", "autonomy_denied")),
                resolved_at=datetime.now(UTC),
            )
            self._save_request(request, result, risk, None)
            self._emit_forget(result, "memory_forget_blocked", 0.9)
            return result

        affected, preserved, forgotten = self._execute_forget(request)
        result = _result(
            request,
            forget_id,
            status="completed" if forgotten else "failed",
            forgotten=forgotten,
            approval_required=False,
            approval_request_id=None,
            affected=affected,
            preserved=preserved,
            reason=request.reason if forgotten else "target_not_found_or_not_forgotten",
            resolved_at=datetime.now(UTC),
        )
        self._save_request(request, result, risk, None)
        self._emit_forget(result, "memory_forgotten" if forgotten else "memory_forget_blocked", 0.2)
        return result

    def get_result(self, forget_request_id: str) -> ForgetMemoryResult | None:
        """Return one forget result."""
        record = self._repository.get_forgetting_request(forget_request_id)
        if record is None:
            return None
        return ForgetMemoryResult(
            forget_request_id=record.forget_request_id,
            target_type=record.target_type,
            target_id=record.target_id,
            status=record.status,
            forgotten=bool(record.result.get("forgotten")),
            approval_required=bool(record.result.get("approval_required")),
            approval_request_id=record.approval_request_id,
            affected_refs=_list_str(record.result.get("affected_refs")),
            preserved_refs=_list_str(record.result.get("preserved_refs")),
            reason=record.reason,
            created_at=record.created_at,
            resolved_at=record.resolved_at,
        )

    def _assess_risk(self, request: ForgetMemoryRequest) -> RiskAssessment | None:
        assess = getattr(self._risk_engine, "assess", None)
        if not callable(assess):
            return None
        result = assess(
            RiskAssessmentRequest(
                trace_id=request.trace_id,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                action_type="memory.forget",
                resource_type=request.target_type,
                resource_id=request.target_id,
                requested_risk_level=_risk_for_target(request.target_type),
                payload={},
                context={
                    "security_scope": request.owner_scope,
                    "deletes_data": True,
                    "approval_present": request.approval_present,
                },
                metadata={"security_scope": request.owner_scope},
            )
        )
        return result if isinstance(result, RiskAssessment) else None

    def _create_approval(
        self,
        request: ForgetMemoryRequest,
        risk: RiskAssessment | None,
        forget_id: str,
    ) -> str | None:
        create = getattr(self._approval_service, "create_request", None)
        if not callable(create):
            return None
        try:
            approval = create(
                ApprovalCreateRequest(
                    trace_id=request.trace_id,
                    actor_id=request.actor_id,
                    workspace_id=request.workspace_id,
                    requested_by=request.requested_by or request.actor_id,
                    action_type="memory.forget.execute",
                    resource_type=request.target_type,
                    resource_id=request.target_id,
                    title=f"Approval required for memory forget {request.target_id}",
                    description="AION requires approval before forgetting this memory target.",
                    risk_assessment_id=(risk.risk_assessment_id if risk is not None else None),
                    priority="high",
                    approval_scope=request.owner_scope,
                    payload={"forget_request_id": forget_id, "target_type": request.target_type},
                    constraints=["memory_forgetting_requires_approval"],
                )
            )
        except Exception:
            return None
        return str(getattr(approval, "approval_request_id", "")) or None

    def _execute_forget(self, request: ForgetMemoryRequest) -> tuple[list[str], list[str], bool]:
        preserved = _preserved_refs(self._memory_service, request)
        if request.target_type == "memory":
            deleted = _call_bool(self._memory_service, "delete", request.target_id)
            _call_bool(
                self._semantic_memory_service,
                "forget",
                request.target_id,
                request.owner_scope,
            )
            return ([request.target_id] if deleted else []), preserved, deleted
        if request.target_type == "semantic_index":
            deleted = _call_bool(
                self._semantic_memory_service,
                "forget",
                request.target_id,
                request.owner_scope,
            )
            return ([request.target_id] if deleted else []), preserved, deleted
        if request.target_type == "graph_node":
            deleted = _call_bool(
                self._graph_memory_service,
                "delete_node",
                request.target_id,
                request.owner_scope,
            )
            return ([request.target_id] if deleted else []), preserved, deleted
        if request.target_type == "graph_edge":
            deleted = _call_bool(
                self._graph_memory_service,
                "delete_edge",
                request.target_id,
                request.owner_scope,
            )
            return ([request.target_id] if deleted else []), preserved, deleted
        if request.target_type == "evidence_link":
            deleted = _call_bool(self._evidence_service, "soft_delete_link", request.target_id)
            return ([request.target_id] if deleted else []), preserved, deleted
        if request.target_type == "skill":
            deleted = _call_bool(self._skill_service, "archive", request.target_id)
            return ([request.target_id] if deleted else []), preserved, deleted
        if request.target_type == "skill_candidate":
            deleted = _call_bool(self._skill_service, "reject_candidate", request.target_id)
            return ([request.target_id] if deleted else []), preserved, deleted
        return [], preserved, False

    def _autonomy_decision(self, request: ForgetMemoryRequest) -> object | None:
        decide = getattr(self._autonomy_governor, "decide", None)
        if not callable(decide):
            return None
        return cast(
            object,
            decide(
                AutonomyDecisionRequest(
                    trace_id=request.trace_id,
                    actor_id=request.actor_id,
                    workspace_id=request.workspace_id,
                    requested_mode="dry_run",
                    action_type="memory.forget.execute",
                    resource_type=request.target_type,
                    resource_id=request.target_id,
                    risk_level=_risk_for_target(request.target_type),
                    approval_present=request.approval_present,
                    delegation_id=_metadata_str(request.metadata, "delegation_id"),
                    context={"security_scope": request.owner_scope},
                    metadata=request.metadata,
                )
            ),
        )

    def _save_request(
        self,
        request: ForgetMemoryRequest,
        result: ForgetMemoryResult,
        risk: RiskAssessment | None,
        approval_id: str | None,
    ) -> None:
        self._repository.save_forgetting_request(
            MemoryForgettingRequestRecord(
                forget_request_id=result.forget_request_id,
                trace_id=request.trace_id,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                target_type=request.target_type,
                target_id=request.target_id,
                owner_scope=request.owner_scope,
                reason=result.reason,
                status=result.status,
                risk_assessment_id=risk.risk_assessment_id if risk is not None else None,
                approval_request_id=approval_id or result.approval_request_id,
                result=result.model_dump(mode="json"),
                requested_by=request.requested_by,
                created_at=result.created_at,
                resolved_at=result.resolved_at,
            )
        )

    def _emit_forget(
        self,
        result: ForgetMemoryResult,
        event_type: str,
        intensity: float,
    ) -> None:
        if self._telemetry_service is None:
            return
        event = VisualTelemetryEvent(
            telemetry_id=f"telemetry-{result.forget_request_id}-{event_type}",
            trace_id=result.forget_request_id,
            event_type=cast(Any, event_type),
            node_type="memory",
            node_id=result.target_id,
            edge_from=result.forget_request_id,
            edge_to=result.target_id,
            intensity=intensity,
            payload=result.model_dump(mode="json"),
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


def _result(
    request: ForgetMemoryRequest,
    forget_id: str,
    *,
    status: str,
    forgotten: bool,
    approval_required: bool,
    approval_request_id: str | None,
    affected: list[str],
    preserved: list[str],
    reason: str,
    resolved_at: datetime | None,
) -> ForgetMemoryResult:
    return ForgetMemoryResult(
        forget_request_id=forget_id,
        target_type=request.target_type,
        target_id=request.target_id,
        status=cast(Any, status),
        forgotten=forgotten,
        approval_required=approval_required,
        approval_request_id=approval_request_id,
        affected_refs=affected,
        preserved_refs=preserved,
        reason=reason,
        created_at=datetime.now(UTC),
        resolved_at=resolved_at,
    )


def _risk_for_target(target_type: str) -> RiskLevel:
    return "high" if target_type in {"memory", "graph_node", "graph_edge", "skill"} else "medium"


def _preserved_refs(memory_service: object | None, request: ForgetMemoryRequest) -> list[str]:
    if request.target_type != "memory":
        return []
    get = getattr(memory_service, "get", None)
    if not callable(get):
        return []
    memory = get(request.target_id)
    if not isinstance(memory, MemoryRecord):
        return []
    refs: list[str] = []
    if memory.content_ref:
        refs.append(memory.content_ref)
    evidence_refs = memory.metadata.get("evidence_refs")
    if isinstance(evidence_refs, list):
        refs.extend(str(item) for item in evidence_refs)
    return sorted(set(refs))


def _metadata_str(metadata: dict[str, Any], key: str) -> str | None:
    value = metadata.get(key)
    return value if isinstance(value, str) and value else None


def _call_bool(target: object | None, method_name: str, *args: object) -> bool:
    method = getattr(target, method_name, None)
    if not callable(method):
        return False
    try:
        return bool(method(*args))
    except Exception:
        return False


def _list_str(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return []
