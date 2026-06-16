"""Retry policy registry service."""

from __future__ import annotations

import random
from datetime import UTC, datetime
from typing import Any, cast

from aion_brain.api_support.errors import AIONNotFoundException
from aion_brain.contracts.resilience import RetryPolicy
from aion_brain.policy.base import PolicyAdapter
from aion_brain.resilience._shared import authorize, emit_resilience_event
from aion_brain.resilience.defaults import default_retry_policies
from aion_brain.resilience.repository import ResilienceRepository


class RetryPolicyService:
    """Policy-gated bounded retry policy registry."""

    def __init__(
        self,
        repository: ResilienceRepository,
        policy_adapter: PolicyAdapter,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def create_policy(self, policy: RetryPolicy) -> RetryPolicy:
        """Create or replace a retry policy."""
        authorize(
            self._policy_adapter,
            "resilience.retry_policy.create",
            policy.owner_scope,
            actor_id=policy.created_by,
            resource_type="retry_policy",
            resource_id=policy.name,
            risk_level="medium",
        )
        now = datetime.now(UTC)
        saved = self._repository.save_retry_policy(
            policy.model_copy(
                update={
                    "created_at": policy.created_at or now,
                    "updated_at": now,
                    "disabled_at": policy.disabled_at,
                }
            )
        )
        emit_resilience_event(
            self._telemetry_service,
            event_type="retry_policy_registered",
            node_type="retry_policy",
            node_id=saved.name,
            intensity=0.4,
            payload={"target_type": saved.target_type},
        )
        return saved

    def get_policy(self, name: str) -> RetryPolicy | None:
        """Return one retry policy by name."""
        authorize(
            self._policy_adapter,
            "resilience.retry_policy.read",
            ["workspace:main"],
            resource_type="retry_policy",
            resource_id=name,
        )
        return self._repository.get_retry_policy(name)

    def list_policies(
        self,
        status: str | None = None,
        target_type: str | None = None,
    ) -> list[RetryPolicy]:
        """List retry policies."""
        authorize(
            self._policy_adapter,
            "resilience.retry_policy.read",
            ["workspace:main"],
            context={"status": status, "target_type": target_type},
        )
        return self._repository.list_retry_policies(status=status, target_type=target_type)

    def disable_policy(self, name: str, actor_id: str | None, reason: str) -> RetryPolicy:
        """Disable one retry policy."""
        authorize(
            self._policy_adapter,
            "resilience.retry_policy.update",
            ["workspace:main"],
            actor_id=actor_id,
            resource_type="retry_policy",
            resource_id=name,
            risk_level="medium",
            context={"reason": reason},
        )
        policy = self._repository.get_retry_policy(name)
        if policy is None:
            raise AIONNotFoundException("retry_policy_not_found")
        return self._repository.save_retry_policy(
            policy.model_copy(
                update={
                    "status": cast(Any, "disabled"),
                    "disabled_at": datetime.now(UTC),
                    "metadata": {**policy.metadata, "disable_reason": reason},
                }
            )
        )

    def seed_defaults(self, dry_run: bool = True) -> dict[str, Any]:
        """Seed default retry policies or report what would be seeded."""
        policies = default_retry_policies()
        if dry_run:
            return {
                "dry_run": True,
                "policy_count": len(policies),
                "policies": [policy.model_dump(mode="json") for policy in policies],
            }
        saved = [self.create_policy(policy) for policy in policies]
        return {
            "dry_run": False,
            "policy_count": len(saved),
            "policies": [policy.model_dump(mode="json") for policy in saved],
        }

    def compute_delay_ms(self, policy: RetryPolicy, attempt: int) -> int:
        """Compute bounded retry delay for one attempt."""
        bounded_attempt = max(1, attempt)
        base = policy.initial_delay_ms * (policy.backoff_multiplier ** max(0, bounded_attempt - 1))
        delay = min(policy.max_delay_ms, int(base))
        if policy.jitter_enabled:
            seed = policy.metadata.get("seed", f"{policy.name}:{bounded_attempt}")
            rng = random.Random(str(seed))
            delay = int(delay * (0.5 + rng.random() * 0.5))
        return max(0, delay)

    def should_retry(self, policy: RetryPolicy, status: str, attempt: int) -> bool:
        """Return whether a status should retry on this attempt."""
        if policy.status != "active":
            return False
        if attempt >= policy.max_attempts:
            return False
        if status in policy.non_retryable_statuses:
            return False
        if policy.retryable_statuses and status not in policy.retryable_statuses:
            return False
        return True

    def policy_for_target(self, target_type: str) -> RetryPolicy | None:
        """Return the first active policy for a target type."""
        policies = self._repository.list_retry_policies(
            status="active",
            target_type=target_type,
        )
        if policies:
            return policies[0]
        for policy in default_retry_policies():
            if policy.target_type == target_type:
                return policy
        return None
