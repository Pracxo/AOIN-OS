"""Explicit local workflow worker tick."""

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.autonomy import AutonomyDecisionRequest
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.contracts.workflows import WorkflowHeartbeat, WorkflowWorkerRecord
from aion_brain.workflows.repository import WorkflowRepository


class LocalWorkflowWorker:
    """Poll and run pending workflow runs only when explicitly invoked."""

    def __init__(
        self,
        *,
        repository: WorkflowRepository,
        engine: object,
        enabled: bool,
        max_runs_per_tick: int,
        policy_adapter: object | None = None,
        telemetry_service: object | None = None,
        worker_id: str = "local-workflow-worker",
        autonomy_governor: object | None = None,
    ) -> None:
        self._repository = repository
        self._engine = engine
        self._enabled = enabled
        self._max_runs_per_tick = max_runs_per_tick
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._worker_id = worker_id
        self._autonomy_governor = autonomy_governor

    def start_once(self, max_runs: int | None = None) -> dict[str, Any]:
        """Run one bounded polling tick."""
        if not self._enabled:
            return {"status": "skipped", "reason": "workflow_local_worker_disabled", "ran": 0}
        autonomy = self._autonomy_decision()
        if autonomy is not None and not bool(getattr(autonomy, "allow", False)):
            return {
                "status": "blocked_by_autonomy",
                "reason": str(getattr(autonomy, "reason", "autonomy_denied")),
                "ran": 0,
            }
        limit = max(0, max_runs if max_runs is not None else self._max_runs_per_tick)
        self._save_worker("running")
        self.heartbeat(self._worker_id, None, "running", {"max_runs": limit})
        runs = self._repository.list_runnable_runs(limit=limit, now=datetime.now(UTC))
        ran = 0
        errors: list[dict[str, Any]] = []
        run_existing = getattr(self._engine, "run_existing", None)
        for run in runs:
            if not callable(run_existing):
                errors.append(
                    {
                        "workflow_run_id": run.workflow_run_id,
                        "reason": "engine_unavailable",
                    }
                )
                continue
            try:
                self.heartbeat(
                    self._worker_id,
                    run.workflow_run_id,
                    "running",
                    {"workflow_id": run.workflow_id},
                )
                run_existing(run.workflow_run_id)
                ran += 1
            except Exception as exc:
                errors.append({"workflow_run_id": run.workflow_run_id, "reason": str(exc)})
        self._save_worker("idle")
        self._emit("workflow_worker_tick", "worker", self._worker_id, 0.5, {"ran": ran})
        return {"status": "completed", "ran": ran, "errors": errors}

    def heartbeat(
        self,
        worker_id: str,
        workflow_run_id: str | None,
        status: str,
        payload: dict[str, Any],
    ) -> WorkflowHeartbeat:
        """Persist one worker heartbeat."""
        self._authorize_heartbeat(worker_id, workflow_run_id)
        heartbeat = WorkflowHeartbeat(
            heartbeat_id=f"workflow-heartbeat-{uuid4().hex}",
            workflow_run_id=workflow_run_id,
            worker_id=worker_id,
            status=status,
            payload=payload,
            created_at=datetime.now(UTC),
        )
        saved = self._repository.save_heartbeat(heartbeat)
        self._emit(
            "workflow_heartbeat_recorded",
            "worker",
            worker_id,
            0.4,
            {"workflow_run_id": workflow_run_id, "status": status},
        )
        return saved

    def _save_worker(self, status: str) -> None:
        now = datetime.now(UTC)
        self._repository.save_worker(
            WorkflowWorkerRecord(
                worker_id=self._worker_id,
                worker_type="local_workflow",
                status=status,  # type: ignore[arg-type]
                last_heartbeat_at=now,
                capabilities=["workflow.run"],
                metadata={"bounded_tick": True},
                started_at=now if status == "running" else None,
                stopped_at=now if status == "stopped" else None,
                created_at=now,
                updated_at=now,
            )
        )

    def _emit(
        self,
        event_type: str,
        node_type: str,
        node_id: str,
        intensity: float,
        payload: dict[str, Any],
    ) -> None:
        if self._telemetry_service is None:
            return
        event = VisualTelemetryEvent(
            telemetry_id=f"telemetry-{node_id}-{event_type}",
            trace_id=node_id,
            event_type=event_type,  # type: ignore[arg-type]
            node_type=node_type,  # type: ignore[arg-type]
            node_id=node_id,
            edge_from=None,
            edge_to=node_id,
            intensity=intensity,
            payload=payload,
            created_at=datetime.now(UTC),
        )
        emit = getattr(self._telemetry_service, "emit", None)
        if callable(emit):
            emit(event)

    def _authorize_heartbeat(self, worker_id: str, workflow_run_id: str | None) -> None:
        authorize = getattr(self._policy_adapter, "authorize", None)
        if not callable(authorize):
            return
        decision = authorize(
            PolicyRequest(
                request_id=f"workflow.heartbeat.write-{worker_id}-{uuid4().hex}",
                trace_id=workflow_run_id,
                actor_id="aion-system",
                workspace_id=None,
                action_type="workflow.heartbeat.write",
                resource_type="workflow_heartbeat",
                resource_id=workflow_run_id,
                risk_level="medium",
                approval_present=True,
                requested_permissions=[],
                security_scope=["workspace:main"],
                context={"worker_id": worker_id},
            )
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")

    def _autonomy_decision(self) -> object | None:
        decide = getattr(self._autonomy_governor, "decide", None)
        if not callable(decide):
            return None
        return cast(
            object,
            decide(
                AutonomyDecisionRequest(
                    actor_id="aion-system",
                    workspace_id=None,
                    requested_mode="dry_run",
                    action_type="workflow.worker.start",
                    resource_type="worker",
                    resource_id=self._worker_id,
                    risk_level="medium",
                    approval_present=False,
                    context={"security_scope": ["workspace:main"], "background_workflow": True},
                    metadata={"worker_id": self._worker_id},
                )
            ),
        )
