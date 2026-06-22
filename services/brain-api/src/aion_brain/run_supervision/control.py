"""Manual run control request service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.contracts.run_control import RunControlRequest, RunControlRequestCreateRequest
from aion_brain.contracts.run_supervision import RunSupervisionRecord
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry

_HIGH_RISK_CONTROL_TYPES = {"cancel", "mark_failed", "mark_completed"}


class RunControlService:
    """Create and hand off run control requests through policy gates."""

    def __init__(
        self,
        repository: object,
        target_adapter: object,
        policy_adapter: object | None,
        *,
        approval_service: object | None = None,
        telemetry_service: object | None = None,
        settings: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._target_adapter = target_adapter
        self._policy_adapter = policy_adapter
        self._approval_service = approval_service
        self._telemetry_service = telemetry_service
        self._settings = settings
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> RunControlService:
        return RunControlService(
            self._repository,
            self._target_adapter,
            self._policy_adapter,
            approval_service=self._approval_service,
            telemetry_service=self._telemetry_service,
            settings=self._settings,
            actor_context=actor_context,
        )

    def request_control(self, request: RunControlRequestCreateRequest) -> RunControlRequest:
        if self._settings is not None and not bool(
            getattr(self._settings, "run_control_enabled", True)
        ):
            raise RuntimeError("run_control_disabled")
        run = _require_run(self._repository, request.run_supervision_id)
        risk_level = "high" if request.control_type in _HIGH_RISK_CONTROL_TYPES else "medium"
        authorize(
            self._policy_adapter,
            action_type="run_supervision.control.request",
            resource_type="run_control_request",
            resource_id=request.run_control_request_id,
            scope=run.owner_scope,
            trace_id=request.trace_id or run.trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            risk_level=risk_level,
            approval_present=request.approval_present,
            context={
                "control_type": request.control_type,
                "requested_mode": request.requested_mode,
            },
        )
        status = "requested"
        result: dict[str, Any] = {"dry_run": request.requested_mode == "dry_run", "executed": False}
        approval_request_id = None
        blocker_refs: list[str] = []
        if risk_level in {"high", "critical"} and not request.approval_present:
            status = "waiting_for_approval"
            approval_request_id = self._create_approval(run, request)
            result["approval_required"] = True
        elif request.requested_mode == "controlled" and not bool(
            getattr(self._settings, "run_control_controlled_enabled", False)
        ):
            status = "blocked"
            blocker_refs.append("run_control_controlled_disabled")
            result["reason"] = "run_control_controlled_disabled"
        elif not bool(
            getattr(self._target_adapter, "supports_control", lambda *_: False)(
                run.target_system, request.control_type
            )
        ):
            status = "unsupported"
            result["reason"] = "target_control_unsupported"
        control = RunControlRequest(
            run_control_request_id=request.run_control_request_id or f"run-control-{uuid4().hex}",
            run_supervision_id=run.run_supervision_id,
            trace_id=request.trace_id or run.trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            control_type=request.control_type,
            status=status,  # type: ignore[arg-type]
            reason=request.reason,
            requested_mode=request.requested_mode,
            target_system=run.target_system,
            target_run_id=run.target_run_id,
            approval_request_id=approval_request_id,
            blocker_refs=blocker_refs,
            result=result,
            metadata={**request.metadata, "control_requests_do_not_execute_themselves": True},
            created_by=request.created_by or self._actor_context.actor_id,
            created_at=datetime.now(UTC),
            completed_at=datetime.now(UTC) if status in {"blocked", "unsupported"} else None,
        )
        stored = _save_control(self._repository, control)
        emit_telemetry(
            self._telemetry_service,
            event_type="run_control_requested",
            node_type="run_control",
            node_id=stored.run_control_request_id,
            intensity=0.7,
            trace_id=stored.trace_id,
            edge_from=run.run_supervision_id,
            edge_to=stored.run_control_request_id,
            payload={"status": stored.status, "control_type": stored.control_type},
        )
        return stored

    def list_requests(
        self,
        run_supervision_id: str | None = None,
        status: str | None = None,
        control_type: str | None = None,
        limit: int = 100,
    ) -> list[RunControlRequest]:
        list_requests = getattr(self._repository, "list_control_requests", None)
        if not callable(list_requests):
            return []
        result = list_requests(
            run_supervision_id=run_supervision_id,
            status=status,
            control_type=control_type,
            limit=limit,
        )
        return [item for item in result if isinstance(item, RunControlRequest)]

    def handoff_control(
        self, run_control_request_id: str, approval_present: bool = False
    ) -> RunControlRequest:
        control = _require_control(self._repository, run_control_request_id)
        run = _require_run(self._repository, control.run_supervision_id)
        authorize(
            self._policy_adapter,
            action_type="run_supervision.control.handoff",
            resource_type="run_control_request",
            resource_id=run_control_request_id,
            scope=run.owner_scope,
            trace_id=control.trace_id,
            actor_id=control.actor_id or self._actor_context.actor_id,
            workspace_id=control.workspace_id or self._actor_context.workspace_id,
            risk_level="high" if control.control_type in _HIGH_RISK_CONTROL_TYPES else "medium",
            approval_present=approval_present,
        )
        if control.requested_mode == "dry_run":
            updated = control.model_copy(
                update={
                    "status": "completed",
                    "result": {
                        **control.result,
                        "planned_target_control": True,
                        "executed": False,
                    },
                    "completed_at": datetime.now(UTC),
                }
            )
        elif not bool(getattr(self._settings, "run_control_controlled_enabled", False)):
            updated = control.model_copy(
                update={
                    "status": "blocked",
                    "result": {
                        **control.result,
                        "reason": "run_control_controlled_disabled",
                        "executed": False,
                    },
                    "completed_at": datetime.now(UTC),
                }
            )
        else:
            updated = control.model_copy(
                update={
                    "status": "handed_off",
                    "result": {"target_control_requested": True, "executed": False},
                    "completed_at": datetime.now(UTC),
                }
            )
        stored = _save_control(self._repository, updated)
        emit_telemetry(
            self._telemetry_service,
            event_type="run_control_blocked"
            if stored.status == "blocked"
            else "run_control_handed_off",
            node_type="run_control",
            node_id=stored.run_control_request_id,
            intensity=1.0 if stored.status == "blocked" else 0.8,
            trace_id=stored.trace_id,
            payload={"status": stored.status, "control_type": stored.control_type},
        )
        return stored

    def _create_approval(
        self, run: RunSupervisionRecord, request: RunControlRequestCreateRequest
    ) -> str:
        create = getattr(self._approval_service, "create_request", None)
        if callable(create):
            try:
                result = create(
                    {
                        "run_supervision_id": run.run_supervision_id,
                        "control_type": request.control_type,
                    }
                )
                approval_id = getattr(result, "approval_request_id", None)
                if isinstance(approval_id, str):
                    return approval_id
            except Exception:
                return "approval_required"
        return "approval_required"


def _require_run(repository: object, run_supervision_id: str) -> RunSupervisionRecord:
    get = getattr(repository, "get_run", None)
    run = get(run_supervision_id) if callable(get) else None
    if not isinstance(run, RunSupervisionRecord):
        raise ValueError("run_supervision_not_found")
    return run


def _require_control(repository: object, run_control_request_id: str) -> RunControlRequest:
    get = getattr(repository, "get_control_request", None)
    control = get(run_control_request_id) if callable(get) else None
    if not isinstance(control, RunControlRequest):
        raise ValueError("run_control_request_not_found")
    return control


def _save_control(repository: object, control: RunControlRequest) -> RunControlRequest:
    save = getattr(repository, "save_control_request", None)
    stored = save(control) if callable(save) else control
    return stored if isinstance(stored, RunControlRequest) else control


__all__ = ["RunControlService"]
