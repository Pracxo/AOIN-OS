"""Lifecycle policy service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from aion_brain.contracts.retention import (
    LifecyclePolicy,
    LifecyclePolicyAction,
    LifecyclePolicyCreateRequest,
    RetentionClass,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.lifecycle.redaction import redact_lifecycle_payload


class LifecyclePolicyService:
    """Manage generic lifecycle policies."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        telemetry_service: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> LifecyclePolicyService:
        return LifecyclePolicyService(
            self._repository,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            actor_context=actor_context,
        )

    def create_policy(self, request: LifecyclePolicyCreateRequest) -> LifecyclePolicy:
        authorize(
            self._policy_adapter,
            action_type="lifecycle.policy.create",
            resource_type="lifecycle_policy",
            resource_id=request.lifecycle_policy_id,
            scope=request.owner_scope,
            actor_id=request.created_by or self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="medium",
            context={"hard_delete_allowed": False},
        )
        now = datetime.now(UTC)
        policy = LifecyclePolicy(
            lifecycle_policy_id=request.lifecycle_policy_id or f"lifecycle-policy-{uuid4().hex}",
            name=request.name,
            description=request.description,
            status="active",
            policy_type=request.policy_type,
            resource_types=request.resource_types,
            source_systems=request.source_systems,
            retention_class=request.retention_class,
            retention_days=request.retention_days,
            review_after_days=request.review_after_days,
            archive_after_days=request.archive_after_days,
            purge_after_days=request.purge_after_days,
            action_on_match=request.action_on_match,
            requires_backup=request.requires_backup,
            requires_approval=request.requires_approval,
            owner_scope=request.owner_scope,
            rule=redact_lifecycle_payload(request.rule),
            metadata=redact_lifecycle_payload({**request.metadata, "hard_delete_allowed": False}),
            created_by=request.created_by or self._actor_context.actor_id,
            created_at=now,
            updated_at=now,
        )
        stored = _save_policy(self._repository, policy)
        emit_telemetry(
            self._telemetry_service,
            event_type="lifecycle_policy_created",
            node_type="lifecycle",
            node_id=stored.lifecycle_policy_id,
            intensity=0.5,
            trace_id=self._actor_context.trace_id,
            payload={"policy_type": stored.policy_type, "retention_class": stored.retention_class},
        )
        return stored

    def get_policy(self, lifecycle_policy_id: str, scope: list[str]) -> LifecyclePolicy | None:
        authorize(
            self._policy_adapter,
            action_type="lifecycle.policy.read",
            resource_type="lifecycle_policy",
            resource_id=lifecycle_policy_id,
            scope=scope,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        get = getattr(self._repository, "get_policy", None)
        policy = get(lifecycle_policy_id) if callable(get) else None
        if not isinstance(policy, LifecyclePolicy):
            return None
        return policy if _scope_matches(policy.owner_scope, scope) else None

    def list_policies(
        self,
        scope: list[str],
        status: str | None = None,
        policy_type: str | None = None,
        retention_class: str | None = None,
        limit: int = 100,
    ) -> list[LifecyclePolicy]:
        authorize(
            self._policy_adapter,
            action_type="lifecycle.policy.read",
            resource_type="lifecycle_policy",
            resource_id=None,
            scope=scope,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        list_items = getattr(self._repository, "list_policies", None)
        if not callable(list_items):
            return []
        policies = list_items(
            scope,
            status=status,
            policy_type=policy_type,
            retention_class=retention_class,
            limit=limit,
        )
        return [item for item in policies if isinstance(item, LifecyclePolicy)]

    def disable_policy(
        self,
        lifecycle_policy_id: str,
        actor_id: str | None,
        reason: str,
    ) -> LifecyclePolicy:
        policy = _require_policy(self._repository, lifecycle_policy_id)
        authorize(
            self._policy_adapter,
            action_type="lifecycle.policy.update",
            resource_type="lifecycle_policy",
            resource_id=lifecycle_policy_id,
            scope=policy.owner_scope,
            actor_id=actor_id or self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="medium",
            context={"reason": reason},
        )
        updated = policy.model_copy(
            update={
                "status": "disabled",
                "disabled_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "metadata": {**policy.metadata, "disable_reason": reason},
            }
        )
        return _save_policy(self._repository, updated)

    def seed_default_policies(self, scope: list[str], dry_run: bool = True) -> dict[str, object]:
        defaults = default_lifecycle_policy_requests(scope)
        if dry_run:
            return {
                "dry_run": True,
                "policy_count": len(defaults),
                "policy_names": [item.name for item in defaults],
                "hard_delete_allowed": False,
            }
        created = [self.create_policy(item) for item in defaults]
        return {
            "dry_run": False,
            "policy_count": len(created),
            "policy_ids": [item.lifecycle_policy_id for item in created],
            "hard_delete_allowed": False,
        }


def default_lifecycle_policy_requests(scope: list[str]) -> list[LifecyclePolicyCreateRequest]:
    """Return generic default lifecycle policies without hard delete."""

    return [
        _default("transient_30_day_review", "transient", 30, "review", scope),
        _default("operational_365_day_review", "operational", 365, "review", scope),
        _default("telemetry_90_day_review", "telemetry", 90, "review", scope),
        _default("registry_365_day_review", "registry", 365, "review", scope),
        _default("learning_365_day_review", "learning", 365, "review", scope),
        _default("release_retain", "release", 3650, "report_only", scope),
        _default("backup_retain", "backup", 3650, "report_only", scope),
        _default("audit_retain", "audit", 3650, "report_only", scope),
        _default("evidence_retain", "evidence", 3650, "report_only", scope),
        _default("memory_review", "memory", 365, "review", scope),
    ]


def _default(
    name: str,
    retention_class: str,
    retention_days: int,
    action: str,
    scope: list[str],
) -> LifecyclePolicyCreateRequest:
    return LifecyclePolicyCreateRequest(
        lifecycle_policy_id=f"lifecycle-policy-{name}",
        name=name,
        description=f"Generic {retention_class} lifecycle policy.",
        policy_type="retention",
        retention_class=cast(RetentionClass, retention_class),
        retention_days=retention_days,
        review_after_days=retention_days,
        action_on_match=cast(LifecyclePolicyAction, action),
        requires_backup=True,
        requires_approval=True,
        owner_scope=scope,
        rule={"source": "aion_default", "hard_delete_allowed": False},
        metadata={"default_policy": True},
    )


def _save_policy(repository: object, policy: LifecyclePolicy) -> LifecyclePolicy:
    save = getattr(repository, "save_policy", None)
    stored = save(policy) if callable(save) else policy
    return stored if isinstance(stored, LifecyclePolicy) else policy


def _require_policy(repository: object, lifecycle_policy_id: str) -> LifecyclePolicy:
    get = getattr(repository, "get_policy", None)
    policy = get(lifecycle_policy_id) if callable(get) else None
    if not isinstance(policy, LifecyclePolicy):
        raise ValueError("lifecycle_policy_not_found")
    return policy


def _scope_matches(owner_scope: list[str], scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(scope))


__all__ = ["LifecyclePolicyService", "default_lifecycle_policy_requests"]
