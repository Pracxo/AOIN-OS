"""Execution handoff gate service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.action_proposals.redaction import redact_action_payload
from aion_brain.contracts.action_proposals import ActionProposal
from aion_brain.contracts.commands import CommandDispatchRequest, CommandTargetType
from aion_brain.contracts.cycles import CognitiveCycleRunRequest
from aion_brain.contracts.execution_handoffs import ExecutionHandoff, ExecutionHandoffRequest
from aion_brain.contracts.modules import CapabilityInvocationRequest
from aion_brain.contracts.sandbox import SandboxRunRequest, SandboxRunTargetType
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.workflows import WorkflowRunRequest
from aion_brain.dialogue._shared import authorize, emit_telemetry


class ExecutionHandoffService:
    """Explicit handoff gate for reviewed action proposals."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        blocker_service: object | None = None,
        command_bus: object | None = None,
        workflow_service: object | None = None,
        execution_orchestrator: object | None = None,
        capability_runtime: object | None = None,
        mcp_service: object | None = None,
        cycle_orchestrator: object | None = None,
        sandbox_service: object | None = None,
        risk_engine: object | None = None,
        autonomy_governor: object | None = None,
        approval_service: object | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
        settings: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._blocker_service = blocker_service
        self._command_bus = command_bus
        self._workflow_service = workflow_service
        self._execution_orchestrator = execution_orchestrator
        self._capability_runtime = capability_runtime
        self._mcp_service = mcp_service
        self._cycle_orchestrator = cycle_orchestrator
        self._sandbox_service = sandbox_service
        self._risk_engine = risk_engine
        self._autonomy_governor = autonomy_governor
        self._approval_service = approval_service
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service
        self._settings = settings
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> ExecutionHandoffService:
        return ExecutionHandoffService(
            self._repository,
            self._policy_adapter,
            blocker_service=self._blocker_service,
            command_bus=self._command_bus,
            workflow_service=self._workflow_service,
            execution_orchestrator=self._execution_orchestrator,
            capability_runtime=self._capability_runtime,
            mcp_service=self._mcp_service,
            cycle_orchestrator=self._cycle_orchestrator,
            sandbox_service=self._sandbox_service,
            risk_engine=self._risk_engine,
            autonomy_governor=self._autonomy_governor,
            approval_service=self._approval_service,
            telemetry_service=self._telemetry_service,
            audit_sink=self._audit_sink,
            provenance_service=self._provenance_service,
            settings=self._settings,
            actor_context=actor_context,
        )

    def handoff(self, request: ExecutionHandoffRequest) -> ExecutionHandoff:
        """Create a handoff record. Dry-run does not call target services."""

        if self._settings is not None and not bool(
            getattr(self._settings, "execution_handoff_enabled", True)
        ):
            raise RuntimeError("execution_handoff_disabled")
        proposal = _require_proposal(self._repository, request.action_proposal_id)
        authorize(
            self._policy_adapter,
            action_type="action_proposal.handoff",
            resource_type="execution_handoff",
            resource_id=request.execution_handoff_id,
            scope=proposal.owner_scope,
            trace_id=request.trace_id or proposal.trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            risk_level=proposal.risk_level,
            approval_present=request.approval_present,
            context={"mode": request.mode, "target_system": request.target_system},
        )
        blocker_refs: list[str] = []
        status = "dry_run"
        result: dict[str, Any] = {"dry_run": request.mode == "dry_run", "accepted_by_target": False}
        if request.mode != "dry_run" and proposal.status != "approved_for_handoff":
            blocker_refs.append(
                self._create_blocker(
                    proposal,
                    blocker_type="approval_required",
                    severity="high",
                    reason="proposal_not_approved_for_handoff",
                )
            )
            status = "blocked"
        elif request.target_system == "mcp_adapter" and not bool(
            getattr(self._settings, "mcp_controlled_invocation_enabled", False)
        ):
            blocker_refs.append(
                self._create_blocker(
                    proposal,
                    blocker_type="runtime_config_disabled",
                    severity="high",
                    reason="mcp_handoff_disabled",
                )
            )
            status = "blocked"
        elif request.mode == "controlled" and not bool(
            getattr(self._settings, "action_handoff_controlled_enabled", False)
        ):
            blocker_refs.append(
                self._create_blocker(
                    proposal,
                    blocker_type="runtime_config_disabled",
                    severity="high",
                    reason="controlled_handoff_disabled",
                )
            )
            status = "blocked"
        elif (
            request.mode == "controlled"
            and proposal.risk_level in {"high", "critical"}
            and not request.approval_present
        ):
            blocker_refs.append(
                self._create_blocker(
                    proposal,
                    blocker_type="approval_required",
                    severity=proposal.risk_level,
                    reason="approval_required_before_controlled_handoff",
                )
            )
            status = "waiting_for_approval"
            result["approval_request_id"] = self._approval_request_id(proposal)
        target_payload = self._target_payload(proposal, request)
        handoff = ExecutionHandoff(
            execution_handoff_id=request.execution_handoff_id or f"execution-handoff-{uuid4().hex}",
            action_proposal_id=proposal.action_proposal_id,
            trace_id=request.trace_id or proposal.trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            status=status,  # type: ignore[arg-type]
            handoff_type=request.handoff_type,
            target_system=request.target_system,
            target_request_id=_target_request_id(target_payload),
            target_run_id=None,
            handoff_payload=target_payload,
            policy_decision_id=None,
            risk_assessment_id=None,
            autonomy_decision_id=None,
            approval_request_id=_str_or_none(result.get("approval_request_id")),
            blocker_refs=blocker_refs,
            result=result,
            metadata={**request.metadata, "handoff_does_not_mean_completed": True},
            created_by=request.created_by or self._actor_context.actor_id,
            created_at=datetime.now(UTC),
            completed_at=datetime.now(UTC)
            if status in {"dry_run", "blocked", "unsupported"}
            else None,
        )
        if request.mode == "controlled" and status == "dry_run":
            handoff = self._controlled_handoff(handoff, request.target_system, target_payload)
        stored = _save_handoff(self._repository, handoff)
        if stored.status == "handed_off":
            _save_proposal(
                self._repository,
                proposal.model_copy(
                    update={"status": "handed_off", "updated_at": datetime.now(UTC)}
                ),
            )
        self._record_audit("execution_handoff_created", stored.execution_handoff_id)
        self._record_provenance(
            proposal.action_proposal_id, stored.execution_handoff_id, "handed_off_as"
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="execution_handoff_blocked"
            if stored.status in {"blocked", "waiting_for_approval"}
            else "execution_handoff_created",
            node_type="execution_handoff",
            node_id=stored.execution_handoff_id,
            intensity=1.0
            if stored.status in {"blocked", "waiting_for_approval"}
            else (0.7 if stored.status == "dry_run" else 0.9),
            trace_id=stored.trace_id,
            payload={"status": stored.status, "target_system": stored.target_system},
        )
        return stored

    def get_handoff(self, execution_handoff_id: str, scope: list[str]) -> ExecutionHandoff | None:
        authorize(
            self._policy_adapter,
            action_type="action_proposal.handoff.read",
            resource_type="execution_handoff",
            resource_id=execution_handoff_id,
            scope=scope,
            risk_level="low",
        )
        get = getattr(self._repository, "get_handoff", None)
        handoff = get(execution_handoff_id) if callable(get) else None
        return handoff if isinstance(handoff, ExecutionHandoff) else None

    def list_handoffs(
        self,
        action_proposal_id: str | None = None,
        status: str | None = None,
        target_system: str | None = None,
        limit: int = 100,
    ) -> list[ExecutionHandoff]:
        list_handoffs = getattr(self._repository, "list_handoffs", None)
        if not callable(list_handoffs):
            return []
        result = list_handoffs(
            action_proposal_id=action_proposal_id,
            status=status,
            target_system=target_system,
            limit=limit,
        )
        return [item for item in result if isinstance(item, ExecutionHandoff)]

    def _target_payload(
        self,
        proposal: ActionProposal,
        request: ExecutionHandoffRequest,
    ) -> dict[str, Any]:
        payload, findings = redact_action_payload(proposal.proposed_payload)
        trace_id = request.trace_id or proposal.trace_id
        actor_id = request.actor_id or proposal.actor_id
        workspace_id = request.workspace_id or proposal.workspace_id
        metadata: dict[str, Any] = {
            "action_proposal_id": proposal.action_proposal_id,
            "redaction_findings": findings,
        }
        if request.target_system == "command_bus":
            return CommandDispatchRequest(
                command_id=f"command-{proposal.action_proposal_id}",
                command_type="generic",
                target_type=_command_target_type(proposal.target_type),
                target_id=proposal.target_id,
                trace_id=trace_id,
                actor_id=actor_id,
                workspace_id=workspace_id,
                mode=request.mode,
                payload=payload,
                approval_present=request.approval_present,
                owner_scope=proposal.owner_scope,
                metadata=metadata,
                idempotency_key=f"action-proposal:{proposal.action_proposal_id}",
            ).model_dump(mode="python")
        if request.target_system == "workflow_engine":
            return WorkflowRunRequest(
                workflow_run_id=f"workflow-run-{proposal.action_proposal_id}",
                workflow_id=proposal.target_id or proposal.target_type,
                trace_id=trace_id,
                actor_id=actor_id,
                workspace_id=workspace_id,
                mode=request.mode,
                input=payload,
                approval_present=request.approval_present,
                metadata=metadata,
            ).model_dump(mode="python")
        if request.target_system == "capability_runtime":
            return CapabilityInvocationRequest(
                invocation_id=f"capability-invocation-{proposal.action_proposal_id}",
                capability_id=proposal.target_id
                or (
                    proposal.capability_refs[0]
                    if proposal.capability_refs
                    else proposal.target_type
                ),
                trace_id=trace_id,
                actor_id=actor_id,
                workspace_id=workspace_id,
                mode=request.mode,
                payload=payload,
                approval_present=request.approval_present,
                metadata=metadata,
            ).model_dump(mode="python")
        if request.target_system == "cognitive_cycle":
            return CognitiveCycleRunRequest(
                cycle_run_id=f"cycle-run-{proposal.action_proposal_id}",
                cycle_type="maintenance",
                trace_id=trace_id,
                actor_id=actor_id,
                workspace_id=workspace_id,
                mode=request.mode,
                owner_scope=proposal.owner_scope,
                input=payload,
                approval_present=request.approval_present,
                metadata=metadata,
            ).model_dump(mode="python")
        if request.target_system == "sandbox":
            return SandboxRunRequest(
                sandbox_run_id=f"sandbox-run-{proposal.action_proposal_id}",
                sandbox_profile_id=proposal.sandbox_profile_id or "default",
                target_type=_sandbox_target_type(proposal.target_type),
                target_id=proposal.target_id,
                trace_id=trace_id,
                actor_id=actor_id,
                workspace_id=workspace_id,
                mode=request.mode,
                input=payload,
                approval_present=request.approval_present,
                metadata=metadata,
            ).model_dump(mode="python")
        return {
            "target_contract": request.handoff_type,
            "target_system": request.target_system,
            "payload": payload,
            "trace_id": trace_id,
            "actor_id": actor_id,
            "workspace_id": workspace_id,
            "mode": request.mode,
            "approval_present": request.approval_present,
            "metadata": metadata,
        }

    def _controlled_handoff(
        self,
        handoff: ExecutionHandoff,
        target_system: str,
        target_payload: dict[str, Any],
    ) -> ExecutionHandoff:
        service = {
            "command_bus": self._command_bus,
            "workflow_engine": self._workflow_service,
            "execution_orchestrator": self._execution_orchestrator,
            "capability_runtime": self._capability_runtime,
            "mcp_adapter": self._mcp_service,
            "cognitive_cycle": self._cycle_orchestrator,
            "sandbox": self._sandbox_service,
        }.get(target_system)
        method = {
            "command_bus": "dispatch",
            "workflow_engine": "run_workflow",
            "execution_orchestrator": "run",
            "capability_runtime": "invoke",
            "mcp_adapter": "invoke",
            "cognitive_cycle": "run_cycle",
            "sandbox": "run",
        }.get(target_system)
        call = getattr(service, method or "", None)
        if not callable(call):
            return handoff.model_copy(
                update={"status": "unsupported", "result": {"reason": "target_service_unavailable"}}
            )
        result = call(target_payload)
        return handoff.model_copy(
            update={
                "status": "handed_off",
                "target_run_id": _target_run_id(result),
                "result": {"accepted_by_target": True, "target_result_type": type(result).__name__},
                "completed_at": datetime.now(UTC),
            }
        )

    def _create_blocker(
        self,
        proposal: ActionProposal,
        *,
        blocker_type: str,
        severity: str,
        reason: str,
    ) -> str:
        create = getattr(self._blocker_service, "create_blocker", None)
        if not callable(create):
            return reason
        blocker = create(
            action_proposal_id=proposal.action_proposal_id,
            trace_id=proposal.trace_id,
            blocker_type=blocker_type,
            severity=severity,
            reason=reason,
            source_type="execution_handoff",
            source_id=proposal.action_proposal_id,
        )
        return str(getattr(blocker, "action_blocker_id", reason))

    def _approval_request_id(self, proposal: ActionProposal) -> str:
        create = getattr(self._approval_service, "create_request", None)
        if callable(create):
            try:
                result = create({"action_proposal_id": proposal.action_proposal_id})
                request_id = getattr(result, "approval_request_id", None)
                if isinstance(request_id, str):
                    return request_id
            except Exception:
                return "approval_required"
        return "approval_required"

    def _record_audit(self, event_type: str, execution_handoff_id: str) -> None:
        record = getattr(self._audit_sink, "record_event", None)
        if callable(record):
            try:
                record({"event_type": event_type, "execution_handoff_id": execution_handoff_id})
            except Exception:
                return

    def _record_provenance(self, source_id: str, target_id: str, relation_type: str) -> None:
        link = getattr(self._provenance_service, "record_link", None)
        if callable(link):
            try:
                link(source_id, target_id, relation_type)
            except Exception:
                return


def _require_proposal(repository: object, action_proposal_id: str) -> ActionProposal:
    get = getattr(repository, "get_proposal", None)
    proposal = get(action_proposal_id) if callable(get) else None
    if not isinstance(proposal, ActionProposal):
        raise ValueError("action_proposal_not_found")
    return proposal


def _save_handoff(repository: object, handoff: ExecutionHandoff) -> ExecutionHandoff:
    save = getattr(repository, "save_handoff", None)
    stored = save(handoff) if callable(save) else handoff
    return stored if isinstance(stored, ExecutionHandoff) else handoff


def _save_proposal(repository: object, proposal: ActionProposal) -> ActionProposal:
    save = getattr(repository, "save_proposal", None)
    stored = save(proposal) if callable(save) else proposal
    return stored if isinstance(stored, ActionProposal) else proposal


def _command_target_type(value: str) -> CommandTargetType:
    allowed = {
        "brain",
        "event",
        "workflow",
        "task",
        "cycle",
        "memory",
        "capability",
        "model",
        "module",
        "trace",
        "noop",
    }
    return cast(CommandTargetType, value if value in allowed else "noop")


def _sandbox_target_type(value: str) -> SandboxRunTargetType:
    allowed = {"capability", "module", "mcp_tool", "command", "workflow_step", "test"}
    return cast(SandboxRunTargetType, value if value in allowed else "command")


def _target_request_id(payload: dict[str, Any]) -> str | None:
    for key in ("command_id", "workflow_run_id", "invocation_id", "cycle_run_id", "sandbox_run_id"):
        value = payload.get(key)
        if isinstance(value, str):
            return value
    return None


def _target_run_id(result: object) -> str | None:
    for key in ("command_id", "workflow_run_id", "invocation_id", "cycle_run_id", "sandbox_run_id"):
        value = getattr(result, key, None)
        if isinstance(value, str):
            return value
    return None


def _str_or_none(value: object) -> str | None:
    return value if isinstance(value, str) else None


__all__ = ["ExecutionHandoffService"]
