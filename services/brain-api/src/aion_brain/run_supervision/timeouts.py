"""Timeout policy service for supervised runs."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from aion_brain.contracts.action_proposals import ActionBlocker
from aion_brain.contracts.run_supervision import RunSupervisionRecord, RunTimeoutPolicy
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry


class TimeoutPolicyService:
    """Create and evaluate timeout policies without automatic cancellation."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        telemetry_service: object | None = None,
        settings: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._settings = settings
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> TimeoutPolicyService:
        return TimeoutPolicyService(
            self._repository,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            settings=self._settings,
            actor_context=actor_context,
        )

    def create_policy(self, policy: RunTimeoutPolicy) -> RunTimeoutPolicy:
        if self._settings is not None and not bool(
            getattr(self._settings, "run_timeout_policy_enabled", True)
        ):
            raise RuntimeError("run_timeout_policy_disabled")
        authorize(
            self._policy_adapter,
            action_type="run_supervision.timeout_policy.create",
            resource_type="run_timeout_policy",
            resource_id=policy.timeout_policy_id,
            scope=policy.owner_scope,
            actor_id=policy.created_by or self._actor_context.actor_id,
            risk_level="medium",
        )
        save = getattr(self._repository, "save_timeout_policy", None)
        return save(policy) if callable(save) else policy

    def list_policies(
        self,
        scope: list[str],
        status: str | None = None,
        target_system: str | None = None,
        run_type: str | None = None,
    ) -> list[RunTimeoutPolicy]:
        authorize(
            self._policy_adapter,
            action_type="run_supervision.timeout_policy.read",
            resource_type="run_timeout_policy",
            resource_id=None,
            scope=scope,
            risk_level="low",
        )
        list_policies = getattr(self._repository, "list_timeout_policies", None)
        if not callable(list_policies):
            return []
        result = list_policies(
            scope=scope,
            status=status,
            target_system=target_system,
            run_type=run_type,
        )
        return [item for item in result if isinstance(item, RunTimeoutPolicy)]

    def get_policy(self, timeout_policy_id: str, scope: list[str]) -> RunTimeoutPolicy | None:
        authorize(
            self._policy_adapter,
            action_type="run_supervision.timeout_policy.read",
            resource_type="run_timeout_policy",
            resource_id=timeout_policy_id,
            scope=scope,
            risk_level="low",
        )
        get = getattr(self._repository, "get_timeout_policy", None)
        policy = get(timeout_policy_id) if callable(get) else None
        if not isinstance(policy, RunTimeoutPolicy):
            return None
        return policy if _scope_matches(policy.owner_scope, scope) else None

    def disable_policy(
        self, timeout_policy_id: str, actor_id: str | None, reason: str
    ) -> RunTimeoutPolicy:
        policy = self.get_policy(timeout_policy_id, ["workspace:main"])
        if policy is None:
            raise ValueError("timeout_policy_not_found")
        authorize(
            self._policy_adapter,
            action_type="run_supervision.timeout_policy.update",
            resource_type="run_timeout_policy",
            resource_id=timeout_policy_id,
            scope=policy.owner_scope,
            actor_id=actor_id or self._actor_context.actor_id,
            risk_level="medium",
            context={"reason": reason},
        )
        disabled = policy.model_copy(
            update={
                "status": "disabled",
                "disabled_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "metadata": {**policy.metadata, "disabled_reason": reason},
            }
        )
        save = getattr(self._repository, "save_timeout_policy", None)
        return save(disabled) if callable(save) else disabled

    def evaluate(self, run_supervision_id: str, now: datetime | None = None) -> list[ActionBlocker]:
        run = _require_run(self._repository, run_supervision_id)
        detected_at = now or datetime.now(UTC)
        policy = _policy_for_run(self._repository, run)
        if not _timed_out(run, policy, detected_at):
            return []
        blocker = ActionBlocker(
            action_blocker_id=f"run-timeout-blocker-{uuid4().hex}",
            action_proposal_id=None,
            trace_id=run.trace_id,
            blocker_type="generic",
            severity=policy.severity if policy is not None else "medium",
            status="open",
            reason="run_timeout_detected",
            missing_requirement="operator_review",
            source_type="run_supervision",
            source_id=run.run_supervision_id,
            metadata={
                "action_on_timeout": policy.action_on_timeout
                if policy is not None
                else "report_only",
                "auto_cancelled": False,
            },
            created_at=detected_at,
        )
        save_run = getattr(self._repository, "save_run", None)
        if callable(save_run):
            save_run(
                run.model_copy(
                    update={
                        "status": "timed_out",
                        "stalled": True,
                        "updated_at": detected_at,
                        "metadata": {**run.metadata, "timeout_detected": True},
                    }
                )
            )
        emit_telemetry(
            self._telemetry_service,
            event_type="run_timeout_detected",
            node_type="run_supervision",
            node_id=run.run_supervision_id,
            intensity=1.0,
            trace_id=run.trace_id,
            payload={"auto_cancelled": False},
        )
        return [blocker]


def _require_run(repository: object, run_supervision_id: str) -> RunSupervisionRecord:
    get = getattr(repository, "get_run", None)
    run = get(run_supervision_id) if callable(get) else None
    if not isinstance(run, RunSupervisionRecord):
        raise ValueError("run_supervision_not_found")
    return run


def _policy_for_run(repository: object, run: RunSupervisionRecord) -> RunTimeoutPolicy | None:
    if run.timeout_policy_id:
        get_policy = getattr(repository, "get_timeout_policy", None)
        policy = get_policy(run.timeout_policy_id) if callable(get_policy) else None
        return policy if isinstance(policy, RunTimeoutPolicy) else None
    list_policies = getattr(repository, "list_timeout_policies", None)
    if not callable(list_policies):
        return None
    policies = list_policies(
        scope=run.owner_scope,
        status="active",
        target_system=run.target_system,
        run_type=run.run_type,
    )
    return policies[0] if policies else None


def _timed_out(run: RunSupervisionRecord, policy: RunTimeoutPolicy | None, now: datetime) -> bool:
    if run.status not in {"active", "stalled"}:
        return False
    if run.deadline_at is not None and _aware(run.deadline_at) <= _aware(now):
        return True
    if policy is None:
        return False
    anchor = run.created_at or run.last_seen_at
    return anchor is not None and _aware(anchor) + timedelta(
        seconds=policy.timeout_seconds
    ) <= _aware(now)


def _scope_matches(owner_scope: list[str], scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(scope))


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


__all__ = ["TimeoutPolicyService"]
