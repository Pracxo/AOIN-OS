"""Safe generic command handlers."""

from dataclasses import dataclass, field
from typing import Any

from aion_brain.contracts.commands import BrainCommand
from aion_brain.contracts.outbox import OutboxPublishRequest


@dataclass(frozen=True)
class CommandHandlerResult:
    """Internal command handler result."""

    status: str
    result: dict[str, Any] = field(default_factory=dict)
    error: dict[str, Any] = field(default_factory=dict)
    outbox_messages: list[OutboxPublishRequest] = field(default_factory=list)


class CommandHandlerRegistry:
    """Registry of safe, generic command handlers."""

    def __init__(
        self,
        *,
        brain_loop_service: object | None = None,
        event_reaction_router: object | None = None,
        workflow_service: object | None = None,
        task_runner: object | None = None,
        cognitive_cycle_orchestrator: object | None = None,
        memory_governance_engine: object | None = None,
        capability_runtime_gateway: object | None = None,
        model_gateway_service: object | None = None,
    ) -> None:
        self._brain_loop_service = brain_loop_service
        self._event_reaction_router = event_reaction_router
        self._workflow_service = workflow_service
        self._task_runner = task_runner
        self._cognitive_cycle_orchestrator = cognitive_cycle_orchestrator
        self._memory_governance_engine = memory_governance_engine
        self._capability_runtime_gateway = capability_runtime_gateway
        self._model_gateway_service = model_gateway_service

    def execute(self, command: BrainCommand) -> CommandHandlerResult:
        """Execute one command through a safe generic handler."""
        if command.command_type == "noop":
            return CommandHandlerResult(
                status="completed",
                result={"status": "completed", "reason": "noop"},
                outbox_messages=[_lifecycle_message(command, "command.completed")],
            )
        if command.command_type == "generic":
            return CommandHandlerResult(
                status="completed",
                result={"status": "completed", "reason": "generic_command_recorded"},
                outbox_messages=[_lifecycle_message(command, "command.completed")],
            )
        if command.command_type == "event.dispatch":
            return self._event_dispatch(command)
        if command.command_type == "brain.think":
            return self._brain_think(command)
        if command.command_type == "memory.governance":
            return self._memory_governance(command)
        if command.command_type in {
            "brain.plan",
            "brain.execute",
            "workflow.run",
            "task.run",
            "cycle.run",
            "capability.invoke",
            "model.complete",
        }:
            return CommandHandlerResult(
                status="completed" if command.mode == "dry_run" else "failed",
                result={
                    "status": "dry_run" if command.mode == "dry_run" else "not_implemented",
                    "reason": f"{command.command_type}_reserved_for_controlled_adapter",
                },
                error={} if command.mode == "dry_run" else {"reason": "not_implemented"},
                outbox_messages=[_lifecycle_message(command, "command.completed")],
            )
        return CommandHandlerResult(
            status="failed",
            error={"reason": "unknown_command_type"},
        )

    def _event_dispatch(self, command: BrainCommand) -> CommandHandlerResult:
        if self._event_reaction_router is None:
            return CommandHandlerResult(
                status="completed" if command.mode == "dry_run" else "failed",
                result={"status": "dry_run", "reason": "event_router_unavailable"},
                error={} if command.mode == "dry_run" else {"reason": "event_router_unavailable"},
            )
        dispatch = getattr(self._event_reaction_router, "dispatch", None)
        if not callable(dispatch):
            return CommandHandlerResult(status="failed", error={"reason": "dispatch_unavailable"})
        try:
            if command.mode == "dry_run":
                return CommandHandlerResult(
                    status="completed",
                    result={"status": "dry_run", "reason": "event_dispatch_would_run"},
                    outbox_messages=[_lifecycle_message(command, "command.completed")],
                )
            result = dispatch(command.payload)
            payload = (
                result.model_dump(mode="json")
                if hasattr(result, "model_dump")
                else {"result": str(result)}
            )
            return CommandHandlerResult(
                status="completed",
                result={"status": "completed", "dispatch": payload},
                outbox_messages=[_lifecycle_message(command, "command.completed")],
            )
        except Exception as exc:
            return CommandHandlerResult(status="failed", error={"reason": str(exc)})

    def _brain_think(self, command: BrainCommand) -> CommandHandlerResult:
        if command.mode != "dry_run":
            return CommandHandlerResult(
                status="failed",
                error={"reason": "brain_think_controlled_not_available"},
            )
        if self._brain_loop_service is None:
            return CommandHandlerResult(
                status="completed",
                result={"status": "dry_run", "reason": "brain_loop_unavailable"},
            )
        return CommandHandlerResult(
            status="completed",
            result={"status": "dry_run", "reason": "brain_loop_would_run"},
            outbox_messages=[_lifecycle_message(command, "command.completed")],
        )

    def _memory_governance(self, command: BrainCommand) -> CommandHandlerResult:
        if command.mode == "dry_run":
            return CommandHandlerResult(
                status="completed",
                result={"status": "dry_run", "reason": "memory_governance_would_evaluate"},
                outbox_messages=[_lifecycle_message(command, "command.completed")],
            )
        evaluate = getattr(self._memory_governance_engine, "evaluate", None)
        if not callable(evaluate):
            return CommandHandlerResult(status="failed", error={"reason": "not_implemented"})
        try:
            result = evaluate(command.payload)
        except Exception as exc:
            return CommandHandlerResult(status="failed", error={"reason": str(exc)})
        return CommandHandlerResult(
            status="completed",
            result=result.model_dump(mode="json") if hasattr(result, "model_dump") else {},
            outbox_messages=[_lifecycle_message(command, "command.completed")],
        )


def _lifecycle_message(command: BrainCommand, message_type: str) -> OutboxPublishRequest:
    return OutboxPublishRequest(
        message_type=message_type,
        destination="internal",
        subject=f"aion.commands.{command.command_type}",
        payload={
            "command_id": command.command_id,
            "command_type": command.command_type,
            "status": command.status,
        },
        headers={},
        trace_id=command.trace_id,
        correlation_id=command.correlation_id,
        max_attempts=3,
    )
