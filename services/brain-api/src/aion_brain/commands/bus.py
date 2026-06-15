"""AION Command Bus."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.commands.handlers import CommandHandlerRegistry
from aion_brain.commands.repository import CommandRepository
from aion_brain.config import Settings
from aion_brain.contracts.approvals import ApprovalCreateRequest
from aion_brain.contracts.autonomy import AutonomyDecisionRequest, AutonomyRiskLevel
from aion_brain.contracts.commands import (
    BrainCommand,
    CommandDispatchRequest,
    CommandDispatchResult,
    CommandStatus,
)
from aion_brain.contracts.idempotency import IdempotencyCheckRequest
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.risk import RiskAssessmentRequest, RiskLevel
from aion_brain.contracts.sandbox import SandboxRunRequest
from aion_brain.contracts.telemetry import (
    VisualTelemetryEvent,
    VisualTelemetryEventType,
)
from aion_brain.idempotency.service import IdempotencyService
from aion_brain.outbox.service import OutboxService
from aion_brain.policy.base import PolicyAdapter


class CommandBus:
    """Record, gate, and dispatch retry-safe Brain commands."""

    def __init__(
        self,
        *,
        command_repository: CommandRepository,
        command_handlers: CommandHandlerRegistry,
        idempotency_service: IdempotencyService,
        policy_adapter: PolicyAdapter,
        autonomy_governor: object | None,
        risk_engine: object | None,
        approval_service: object | None,
        outbox_service: OutboxService,
        telemetry_service: object | None,
        settings: Settings,
        sandbox_service: object | None = None,
        retry_policy_service: object | None = None,
        audit_sink: object | None = None,
    ) -> None:
        self._repository = command_repository
        self._handlers = command_handlers
        self._idempotency = idempotency_service
        self._policy_adapter = policy_adapter
        self._autonomy_governor = autonomy_governor
        self._risk_engine = risk_engine
        self._approval_service = approval_service
        self._outbox = outbox_service
        self._telemetry_service = telemetry_service
        self._settings = settings
        self._sandbox_service = sandbox_service
        self._retry_policy_service = retry_policy_service
        self._audit_sink = audit_sink

    def set_retry_policy_service(self, retry_policy_service: object | None) -> None:
        """Attach retry policy metadata after kernel assembly."""
        self._retry_policy_service = retry_policy_service

    def set_audit_sink(self, audit_sink: object | None) -> None:
        """Attach audit sink after kernel assembly."""
        self._audit_sink = audit_sink

    def retry_metadata(self, attempt: int, status: str) -> dict[str, object]:
        """Return retry metadata for command handling without auto-retrying."""
        policy_for_target = getattr(self._retry_policy_service, "policy_for_target", None)
        compute_delay_ms = getattr(self._retry_policy_service, "compute_delay_ms", None)
        should_retry = getattr(self._retry_policy_service, "should_retry", None)
        if not (
            callable(policy_for_target)
            and callable(compute_delay_ms)
            and callable(should_retry)
        ):
            return {"retry_configured": False}
        try:
            policy = policy_for_target("command")
            if policy is None:
                return {"retry_configured": False}
            return {
                "retry_configured": True,
                "policy": policy.name,
                "should_retry": bool(should_retry(policy, status, attempt)),
                "delay_ms": int(compute_delay_ms(policy, attempt)),
            }
        except Exception:
            return {"retry_configured": False}

    def dispatch(self, request: CommandDispatchRequest) -> CommandDispatchResult:
        """Dispatch one command through policy, autonomy, risk, and handler gates."""
        now = datetime.now(UTC)
        if not self._settings.command_bus_enabled:
            command = self._new_command(request, status="blocked_by_policy", now=now)
            command = command.model_copy(update={"error": {"reason": "command_bus_disabled"}})
            return CommandDispatchResult(
                command=command,
                duplicate=False,
                idempotency_key=request.idempotency_key,
                outbox_ids=[],
                message="command_bus_disabled",
                created_at=now,
            )

        idem_request = self._idempotency_request(request)
        if request.idempotency_key and self._settings.idempotency_enabled:
            check = self._idempotency.check(idem_request)
            if check.conflict:
                command = self._repository.save(
                    self._new_command(request, status="duplicate", now=now).model_copy(
                        update={"error": {"reason": "idempotency_conflict"}}
                    )
                )
                result = self._result(command, True, [], "idempotency_conflict")
                self._idempotency.fail(request.idempotency_key, command.error)
                return result
            if check.duplicate and check.record is not None and check.record.response:
                try:
                    stored = CommandDispatchResult.model_validate(check.record.response)
                    return stored.model_copy(update={"duplicate": True})
                except Exception:
                    existing_command = self._repository.get_by_idempotency_key(
                        request.idempotency_key
                    )
                    if existing_command is not None:
                        return self._result(existing_command, True, [], "duplicate_suppressed")
            if check.record is None or check.record.status == "expired":
                self._idempotency.start(idem_request)

        command = self._repository.save(self._new_command(request, status="pending", now=now))
        self._emit("command_created", command, 0.5)
        self._audit_command(command, "command_created", "completed")

        policy = self._policy(command, request)
        command = self._repository.save(
            command.model_copy(update={"policy_decision_id": policy.decision_id})
        )
        if not policy.allow and not policy.approval_required:
            return self._finish_blocked(
                command,
                request,
                "blocked_by_policy",
                {"reason": policy.reason, "constraints": policy.constraints},
            )

        autonomy = self._autonomy(command, request)
        if autonomy is not None:
            command = self._repository.save(
                command.model_copy(
                    update={"autonomy_decision_id": getattr(autonomy, "autonomy_decision_id", None)}
                )
            )
            if not bool(getattr(autonomy, "allow", True)):
                return self._finish_blocked(
                    command,
                    request,
                    "blocked_by_autonomy",
                    {
                        "reason": str(getattr(autonomy, "reason", "autonomy_denied")),
                        "constraints": list(getattr(autonomy, "constraints", [])),
                    },
                )

        risk = self._risk(command, request)
        approval_required = policy.approval_required
        if risk is not None:
            command = self._repository.save(
                command.model_copy(
                    update={"risk_assessment_id": getattr(risk, "risk_assessment_id", None)}
                )
            )
            risk_decision = str(getattr(risk, "decision", "allow"))
            if risk_decision == "block":
                return self._finish_blocked(
                    command,
                    request,
                    "blocked_by_policy",
                    {"reason": "risk_blocked"},
                )
            approval_required = approval_required or risk_decision == "require_approval"

        sandbox_error = self._sandbox_boundary_error(command, request)
        if sandbox_error is not None:
            return self._finish_blocked(command, request, "blocked_by_policy", sandbox_error)

        if approval_required and not request.approval_present:
            approval_id = self._create_approval(command, request)
            waiting = self._repository.save(
                command.model_copy(
                    update={
                        "status": "waiting_for_approval",
                        "approval_request_id": approval_id,
                        "result": {"approval_required": True},
                        "completed_at": datetime.now(UTC),
                    }
                )
            )
            return self._complete_idempotency(
                request,
                self._result(waiting, False, [], "approval_required"),
            )

        running = self._repository.save(
            command.model_copy(update={"status": "running", "started_at": datetime.now(UTC)})
        )
        self._emit("command_started", running, 0.6)
        handler_result = self._handlers.execute(running)
        outbox_ids = []
        for message in handler_result.outbox_messages:
            try:
                outbox_ids.append(self._outbox.enqueue(message).outbox_id)
            except Exception:
                continue
        final_status = cast(CommandStatus, handler_result.status)
        final = self._repository.save(
            running.model_copy(
                update={
                    "status": final_status,
                    "result": handler_result.result,
                    "error": handler_result.error,
                    "completed_at": datetime.now(UTC),
                }
            )
        )
        self._emit(
            "command_completed" if final.status == "completed" else "command_failed",
            final,
            0.9,
        )
        self._audit_command(
            final,
            "command_completed" if final.status == "completed" else "command_failed",
            "completed" if final.status == "completed" else "failed",
        )
        result = self._result(final, False, outbox_ids, final.status)
        return self._complete_idempotency(request, result)

    def get(self, command_id: str) -> BrainCommand | None:
        """Return one command."""
        return self._repository.get(command_id)

    def list_commands(
        self,
        *,
        status: str | None = None,
        command_type: str | None = None,
        trace_id: str | None = None,
        limit: int = 50,
    ) -> list[BrainCommand]:
        """List commands."""
        return self._repository.list(
            status=status,
            command_type=command_type,
            trace_id=trace_id,
            limit=limit,
        )

    def cancel(self, command_id: str, reason: str) -> BrainCommand:
        """Cancel a command without deleting it."""
        command = self._repository.get(command_id)
        if command is None:
            raise ValueError("command_not_found")
        return self._repository.save(
            command.model_copy(
                update={
                    "status": "cancelled",
                    "error": {"reason": reason},
                    "completed_at": datetime.now(UTC),
                }
            )
        )

    def _new_command(
        self,
        request: CommandDispatchRequest,
        *,
        status: CommandStatus,
        now: datetime,
    ) -> BrainCommand:
        return BrainCommand(
            command_id=request.command_id or f"command-{uuid4().hex}",
            trace_id=request.trace_id,
            correlation_id=request.correlation_id,
            idempotency_key=request.idempotency_key,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            command_type=request.command_type,
            target_type=request.target_type,
            target_id=request.target_id,
            mode=request.mode,
            status=status,
            payload=request.payload,
            result={},
            error={},
            policy_decision_id=None,
            autonomy_decision_id=None,
            risk_assessment_id=None,
            approval_request_id=None,
            created_at=now,
            started_at=None,
            completed_at=None,
            updated_at=now,
        )

    def _idempotency_request(self, request: CommandDispatchRequest) -> IdempotencyCheckRequest:
        return IdempotencyCheckRequest(
            idempotency_key=request.idempotency_key or f"command-{request.command_id}",
            route="/brain/commands",
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            request_payload={
                "command_type": request.command_type,
                "target_type": request.target_type,
                "target_id": request.target_id,
                "mode": request.mode,
                "payload": request.payload,
            },
        )

    def _policy(
        self,
        command: BrainCommand,
        request: CommandDispatchRequest,
    ) -> PolicyDecision:
        return self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"command.dispatch-{command.command_id}",
                trace_id=command.trace_id,
                actor_id=command.actor_id,
                workspace_id=command.workspace_id,
                action_type="command.dispatch",
                resource_type=command.target_type,
                resource_id=command.target_id,
                risk_level=_risk_for_command(command),
                approval_present=request.approval_present,
                requested_permissions=[],
                security_scope=request.owner_scope,
                context={
                    "command_type": command.command_type,
                    "mode": command.mode,
                    "metadata": request.metadata,
                },
            )
        )

    def _autonomy(self, command: BrainCommand, request: CommandDispatchRequest) -> object | None:
        if self._autonomy_governor is None:
            return None
        decide = getattr(self._autonomy_governor, "decide", None)
        if not callable(decide):
            return None
        autonomy_request = AutonomyDecisionRequest(
            trace_id=command.trace_id,
            actor_id=command.actor_id,
            workspace_id=command.workspace_id,
            requested_mode="dry_run" if command.mode == "dry_run" else "supervised_controlled",
            action_type=command.command_type,
            resource_type=command.target_type,
            resource_id=command.target_id,
            risk_level=cast(AutonomyRiskLevel, _risk_for_command(command)),
            approval_present=request.approval_present,
            context={"security_scope": request.owner_scope, "mode": command.mode},
            metadata={},
        )
        return cast(object, decide(autonomy_request))

    def _risk(self, command: BrainCommand, request: CommandDispatchRequest) -> object | None:
        if self._risk_engine is None:
            return None
        assess = getattr(self._risk_engine, "assess", None)
        if not callable(assess):
            return None
        risk_request = RiskAssessmentRequest(
            trace_id=command.trace_id,
            actor_id=command.actor_id,
            workspace_id=command.workspace_id,
            action_type=command.command_type,
            resource_type=command.target_type,
            resource_id=command.target_id,
            requested_risk_level=cast(RiskLevel, _risk_for_command(command)),
            payload=command.payload,
            context={
                "security_scope": request.owner_scope,
                "controlled_execution": command.mode == "controlled",
                "approval_present": request.approval_present,
                "dry_run": command.mode == "dry_run",
            },
            metadata={},
        )
        return cast(object, assess(risk_request))

    def _sandbox_boundary_error(
        self,
        command: BrainCommand,
        request: CommandDispatchRequest,
    ) -> dict[str, Any] | None:
        sandbox_profile_id = request.metadata.get("sandbox_profile_id")
        if sandbox_profile_id is None:
            return None
        if self._sandbox_service is None:
            return {"reason": "sandbox_service_unavailable"}
        profile_id = str(sandbox_profile_id)
        target_id = command.target_id or command.command_id
        has_grant = getattr(self._sandbox_service, "has_active_grant", None)
        if callable(has_grant) and not bool(
            has_grant(
                target_type="command",
                target_id=target_id,
                sandbox_profile_id=profile_id,
            )
        ):
            return {"reason": "runtime_permission_grant_required"}
        run = getattr(self._sandbox_service, "run", None)
        if not callable(run):
            return {"reason": "sandbox_service_unavailable"}
        result = run(
            SandboxRunRequest(
                trace_id=command.trace_id,
                actor_id=command.actor_id,
                workspace_id=command.workspace_id,
                sandbox_profile_id=profile_id,
                target_type="command",
                target_id=target_id,
                mode=command.mode,
                input={"command_type": command.command_type},
                approval_present=request.approval_present,
                metadata={"source": "command_bus"},
            )
        )
        status = str(getattr(result, "status", "failed"))
        if status not in {"dry_run", "completed"}:
            return {
                "reason": "sandbox_validation_failed",
                "sandbox_run_id": getattr(result, "sandbox_run_id", None),
                "sandbox_status": status,
            }
        return None

    def _create_approval(
        self,
        command: BrainCommand,
        request: CommandDispatchRequest,
    ) -> str | None:
        if self._approval_service is None:
            return None
        create = getattr(self._approval_service, "create_request", None)
        if not callable(create):
            return None
        approval = create(
            ApprovalCreateRequest(
                trace_id=command.trace_id,
                actor_id=command.actor_id,
                workspace_id=command.workspace_id,
                requested_by=command.actor_id,
                action_type=command.command_type,
                resource_type=command.target_type,
                resource_id=command.target_id,
                title=f"Approve {command.command_type}",
                description="AION Command Bus requires approval before controlled execution.",
                risk_assessment_id=command.risk_assessment_id,
                priority="normal",
                approval_scope=request.owner_scope,
                payload={"command_id": command.command_id},
                constraints=[],
            )
        )
        return str(getattr(approval, "approval_request_id", "")) or None

    def _finish_blocked(
        self,
        command: BrainCommand,
        request: CommandDispatchRequest,
        status: CommandStatus,
        error: dict[str, Any],
    ) -> CommandDispatchResult:
        blocked = self._repository.save(
            command.model_copy(
                update={
                    "status": status,
                    "error": error,
                    "completed_at": datetime.now(UTC),
                }
            )
        )
        self._emit("command_blocked", blocked, 0.9)
        self._audit_command(blocked, "command_blocked", "blocked")
        return self._complete_idempotency(request, self._result(blocked, False, [], status))

    def _result(
        self,
        command: BrainCommand,
        duplicate: bool,
        outbox_ids: list[str],
        message: str,
    ) -> CommandDispatchResult:
        return CommandDispatchResult(
            command=command,
            duplicate=duplicate,
            idempotency_key=command.idempotency_key,
            outbox_ids=outbox_ids,
            message=message,
            created_at=datetime.now(UTC),
        )

    def _complete_idempotency(
        self,
        request: CommandDispatchRequest,
        result: CommandDispatchResult,
    ) -> CommandDispatchResult:
        if request.idempotency_key and self._settings.idempotency_enabled:
            payload = result.model_dump(mode="json")
            if result.command.status == "failed":
                self._idempotency.fail(request.idempotency_key, result.command.error)
            else:
                self._idempotency.complete(request.idempotency_key, payload)
        return result

    def _emit(self, event_type: str, command: BrainCommand, intensity: float) -> None:
        if self._telemetry_service is None:
            return
        event = VisualTelemetryEvent(
            telemetry_id=f"telemetry-{event_type}-{command.command_id}",
            trace_id=command.trace_id or command.command_id,
            event_type=cast(VisualTelemetryEventType, event_type),
            node_type="command",
            node_id=command.command_id,
            edge_from=command.trace_id,
            edge_to=command.command_id,
            intensity=intensity,
            payload={"command_type": command.command_type, "status": command.status},
            created_at=datetime.now(UTC),
        )
        try:
            emit = getattr(self._telemetry_service, "emit", None)
            if callable(emit):
                emit(event)
        except Exception:
            return

    def _audit_command(self, command: BrainCommand, event_type: str, outcome: str) -> None:
        record_audit_event(
            self._audit_sink,
            action_type="command.dispatch",
            resource_type=command.target_type,
            resource_id=command.target_id or command.command_id,
            event_type=event_type,
            outcome=outcome,
            source_component="command_bus",
            trace_id=command.trace_id,
            correlation_id=command.correlation_id,
            actor_id=command.actor_id,
            workspace_id=command.workspace_id,
            command_id=command.command_id,
            policy_decision_id=command.policy_decision_id,
            autonomy_decision_id=command.autonomy_decision_id,
            risk_assessment_id=command.risk_assessment_id,
            approval_request_id=command.approval_request_id,
            payload={
                "command_type": command.command_type,
                "status": command.status,
                "mode": command.mode,
            },
        )


def _risk_for_command(command: BrainCommand) -> str:
    if command.mode == "dry_run":
        return "low"
    if command.command_type in {"brain.execute", "capability.invoke", "model.complete"}:
        return "high"
    return "medium"
