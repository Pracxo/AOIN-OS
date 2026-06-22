"""Schedule policy metadata service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.scheduler import SchedulePolicy
from aion_brain.dialogue._shared import authorize
from aion_brain.scheduler.policy_context import scheduler_policy_context


class SchedulePolicyService:
    """Create and query local scheduler policy metadata."""

    def __init__(self, repository: object, policy_adapter: object | None) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter

    def create_policy(self, policy: SchedulePolicy) -> SchedulePolicy:
        authorize(
            self._policy_adapter,
            action_type="scheduler.policy.create",
            resource_type="schedule_policy",
            resource_id=policy.policy_id,
            scope=policy.owner_scope,
            risk_level="medium",
            context=scheduler_policy_context(
                "scheduler.policy.create",
                policy.owner_scope,
            ),
        )
        now = datetime.now(UTC)
        stored = policy.model_copy(
            update={
                "policy_id": policy.policy_id or f"schedule-policy-{uuid4().hex}",
                "created_at": policy.created_at or now,
                "updated_at": policy.updated_at or now,
            }
        )
        save = getattr(self._repository, "save_policy", None)
        result = save(stored) if callable(save) else stored
        return result if isinstance(result, SchedulePolicy) else stored

    def list_policies(
        self, scope: list[str], *, status: str | None = None, limit: int = 100
    ) -> list[SchedulePolicy]:
        authorize(
            self._policy_adapter,
            action_type="scheduler.policy.read",
            resource_type="schedule_policy",
            resource_id=None,
            scope=scope,
            risk_level="low",
            context=scheduler_policy_context("scheduler.policy.read", scope),
        )
        list_policies = getattr(self._repository, "list_policies", None)
        if not callable(list_policies):
            return []
        result = list_policies(scope=scope, status=status, limit=limit)
        return [item for item in result if isinstance(item, SchedulePolicy)]
