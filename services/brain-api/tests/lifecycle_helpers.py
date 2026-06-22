"""Shared helpers for lifecycle tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.contracts.retention import LifecyclePolicy, LifecyclePolicyCreateRequest
from aion_brain.lifecycle.policies import LifecyclePolicyService
from aion_brain.lifecycle.repository import LifecycleRepository
from tests.kernel_fakes import AllowPolicy
from tests.resource_registry_helpers import descriptor


def repository() -> LifecycleRepository:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return LifecycleRepository(engine=engine)


def policy(
    *,
    lifecycle_policy_id: str = "lifecycle-policy-test",
    retention_class: str = "unknown",
    action_on_match: str = "review",
    review_after_days: int | None = 0,
    archive_after_days: int | None = None,
    purge_after_days: int | None = None,
) -> LifecyclePolicy:
    service = LifecyclePolicyService(repository(), AllowPolicy())
    return service.create_policy(
        LifecyclePolicyCreateRequest(
            lifecycle_policy_id=lifecycle_policy_id,
            name=lifecycle_policy_id,
            description="Generic lifecycle policy for tests.",
            policy_type="retention",
            retention_class=retention_class,
            retention_days=365,
            review_after_days=review_after_days,
            archive_after_days=archive_after_days,
            purge_after_days=purge_after_days,
            action_on_match=action_on_match,
            requires_backup=True,
            requires_approval=True,
            owner_scope=["workspace:main"],
            rule={"hard_delete_allowed": False},
        )
    )


def old_descriptor(resource_id: str = "res-old"):
    old = datetime.now(UTC) - timedelta(days=400)
    return descriptor(resource_id).model_copy(update={"first_seen_at": old, "last_seen_at": old})


__all__ = ["old_descriptor", "policy", "repository"]
