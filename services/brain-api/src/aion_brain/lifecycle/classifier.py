"""Deterministic retention classifier."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from aion_brain.contracts.resource_registry import ResourceDescriptor
from aion_brain.contracts.retention import (
    LifecyclePolicy,
    LifecycleState,
    RetentionClass,
    RetentionClassification,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry

_RESOURCE_RETENTION_CLASS: dict[str, RetentionClass] = {
    "audit_entry": "audit",
    "provenance_link": "audit",
    "evidence": "evidence",
    "evidence_chunk": "evidence",
    "memory": "memory",
    "belief_claim": "memory",
    "resource": "registry",
    "resource_link": "registry",
    "release_package": "release",
    "freeze_gate": "release",
    "backup_job": "backup",
    "performance_sample": "telemetry",
    "visual_telemetry": "telemetry",
    "learning_pattern": "learning",
    "lesson": "learning",
    "runtime_config": "configuration",
}


class RetentionClassifier:
    """Classify registry descriptors without mutating source resources."""

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

    def with_actor_context(self, actor_context: ActorContext) -> RetentionClassifier:
        return RetentionClassifier(
            self._repository,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            actor_context=actor_context,
        )

    def classify_resource(
        self,
        descriptor: ResourceDescriptor,
        policies: list[LifecyclePolicy],
        created_by: str | None = None,
    ) -> RetentionClassification:
        authorize(
            self._policy_adapter,
            action_type="lifecycle.classify",
            resource_type="resource",
            resource_id=descriptor.resource_uri,
            scope=descriptor.owner_scope,
            trace_id=descriptor.trace_id or self._actor_context.trace_id,
            actor_id=created_by or self._actor_context.actor_id,
            workspace_id=descriptor.workspace_id or self._actor_context.workspace_id,
            risk_level="low",
            context={"source_records_mutated": False},
        )
        retention_class = _class_for_resource(descriptor.resource_type)
        matching = _matching_policies(descriptor, retention_class, policies)
        now = datetime.now(UTC)
        base_time = descriptor.last_seen_at or descriptor.first_seen_at or now
        retention_days = min((policy.retention_days for policy in matching), default=365)
        review_days = min(
            (
                policy.review_after_days
                for policy in matching
                if policy.review_after_days is not None
            ),
            default=None,
        )
        archive_days = min(
            (
                policy.archive_after_days
                for policy in matching
                if policy.archive_after_days is not None
            ),
            default=None,
        )
        purge_days = min(
            (policy.purge_after_days for policy in matching if policy.purge_after_days is not None),
            default=None,
        )
        review_after = base_time + timedelta(days=review_days) if review_days is not None else None
        archive_after = (
            base_time + timedelta(days=archive_days) if archive_days is not None else None
        )
        purge_after = base_time + timedelta(days=purge_days) if purge_days is not None else None
        state = _state_for_dates(now, review_after, archive_after, purge_after)
        classification = RetentionClassification(
            classification_id=f"retention-classification-{uuid4().hex}",
            trace_id=descriptor.trace_id or self._actor_context.trace_id,
            resource_uri=descriptor.resource_uri,
            resource_type=descriptor.resource_type,
            resource_id=descriptor.resource_id,
            source_system=descriptor.source_system,
            status="review_required" if state != "current" else "active",
            retention_class=retention_class,
            lifecycle_state=state,
            sensitivity=descriptor.sensitivity,
            policy_refs=[policy.lifecycle_policy_id for policy in matching],
            reasons=[
                f"resource_type:{descriptor.resource_type}",
                "source_resource_not_mutated",
            ],
            retention_until=base_time + timedelta(days=retention_days),
            review_after=review_after,
            archive_after=archive_after,
            purge_after=purge_after,
            owner_scope=descriptor.owner_scope,
            metadata={"source_records_mutated": False},
            created_by=created_by or self._actor_context.actor_id,
            created_at=now,
            updated_at=now,
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="resource_lifecycle_classified",
            node_type="retention_classification",
            node_id=classification.classification_id,
            intensity=0.5,
            trace_id=classification.trace_id,
            payload={
                "resource_type": classification.resource_type,
                "retention_class": classification.retention_class,
                "lifecycle_state": classification.lifecycle_state,
            },
        )
        return classification

    def save_classification(
        self, classification: RetentionClassification
    ) -> RetentionClassification:
        save = getattr(self._repository, "save_classification", None)
        stored = save(classification) if callable(save) else classification
        return stored if isinstance(stored, RetentionClassification) else classification

    def get_classification(
        self, resource_uri: str, scope: list[str]
    ) -> RetentionClassification | None:
        authorize(
            self._policy_adapter,
            action_type="lifecycle.classification.read",
            resource_type="retention_classification",
            resource_id=resource_uri,
            scope=scope,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        get = getattr(self._repository, "get_classification_by_uri", None)
        item = get(resource_uri, scope) if callable(get) else None
        return item if isinstance(item, RetentionClassification) else None

    def list_classifications(
        self,
        scope: list[str],
        retention_class: str | None = None,
        lifecycle_state: str | None = None,
        limit: int = 100,
    ) -> list[RetentionClassification]:
        authorize(
            self._policy_adapter,
            action_type="lifecycle.classification.read",
            resource_type="retention_classification",
            resource_id=None,
            scope=scope,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        list_items = getattr(self._repository, "list_classifications", None)
        if not callable(list_items):
            return []
        classifications = list_items(
            scope,
            retention_class=retention_class,
            lifecycle_state=lifecycle_state,
            limit=limit,
        )
        return [item for item in classifications if isinstance(item, RetentionClassification)]


def _class_for_resource(resource_type: str) -> RetentionClass:
    if resource_type.startswith("registry"):
        return "registry"
    return _RESOURCE_RETENTION_CLASS.get(resource_type, "unknown")


def _matching_policies(
    descriptor: ResourceDescriptor,
    retention_class: RetentionClass,
    policies: list[LifecyclePolicy],
) -> list[LifecyclePolicy]:
    matches = []
    for policy in policies:
        if policy.status != "active":
            continue
        if policy.retention_class not in {retention_class, "unknown"}:
            continue
        if policy.resource_types and descriptor.resource_type not in policy.resource_types:
            continue
        if policy.source_systems and descriptor.source_system not in policy.source_systems:
            continue
        matches.append(policy)
    return matches


def _state_for_dates(
    now: datetime,
    review_after: datetime | None,
    archive_after: datetime | None,
    purge_after: datetime | None,
) -> LifecycleState:
    if purge_after is not None and purge_after <= now:
        return "purge_preview"
    if archive_after is not None and archive_after <= now:
        return "archive_candidate"
    if review_after is not None and review_after <= now:
        return "review_due"
    return "current"


__all__ = ["RetentionClassifier"]
