"""Archive candidate planner."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.action_proposals import ActionProposalCreateRequest
from aion_brain.contracts.lifecycle import ArchiveCandidate
from aion_brain.contracts.resource_registry import ResourceDescriptor
from aion_brain.contracts.retention import LifecyclePolicy, RetentionClassification
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry


class ArchivePlanner:
    """Create archive candidates without executing archive actions."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        action_proposal_service: object | None = None,
        settings: object | None = None,
        telemetry_service: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._action_proposal_service = action_proposal_service
        self._settings = settings
        self._telemetry_service = telemetry_service
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> ArchivePlanner:
        return ArchivePlanner(
            self._repository,
            self._policy_adapter,
            action_proposal_service=self._action_proposal_service,
            settings=self._settings,
            telemetry_service=self._telemetry_service,
            actor_context=actor_context,
        )

    def create_candidate(
        self,
        resource: ResourceDescriptor,
        classification: RetentionClassification,
        policy: LifecyclePolicy,
        reason: str,
        *,
        persist: bool = True,
    ) -> ArchiveCandidate:
        authorize(
            self._policy_adapter,
            action_type="lifecycle.archive_candidate.create",
            resource_type="archive_candidate",
            resource_id=resource.resource_uri,
            scope=resource.owner_scope,
            trace_id=resource.trace_id or self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=resource.workspace_id or self._actor_context.workspace_id,
            risk_level="medium",
            context={"archive_executed": False},
        )
        backup_required = (
            bool(getattr(self._settings, "lifecycle_require_backup_before_archive", True))
            or policy.requires_backup
        )
        candidate = ArchiveCandidate(
            archive_candidate_id=f"archive-candidate-{uuid4().hex}",
            trace_id=resource.trace_id or self._actor_context.trace_id,
            resource_uri=resource.resource_uri,
            resource_type=resource.resource_type,
            resource_id=resource.resource_id,
            source_system=resource.source_system,
            status="proposed",
            severity="medium" if backup_required else "low",
            reason=reason,
            lifecycle_policy_id=policy.lifecycle_policy_id,
            classification_id=classification.classification_id,
            backup_required=backup_required,
            backup_verified=bool(resource.metadata.get("backup_verified", False)),
            owner_scope=resource.owner_scope,
            metadata={"archive_executed": False, "source_records_mutated": False},
            created_by=self._actor_context.actor_id,
            created_at=datetime.now(UTC),
        )
        stored = _save_archive(self._repository, candidate) if persist else candidate
        emit_telemetry(
            self._telemetry_service,
            event_type="archive_candidate_created",
            node_type="archive_candidate",
            node_id=stored.archive_candidate_id,
            intensity=0.7,
            trace_id=stored.trace_id,
            payload={
                "resource_uri": stored.resource_uri,
                "backup_required": stored.backup_required,
            },
        )
        return stored

    def list_candidates(
        self,
        scope: list[str],
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[ArchiveCandidate]:
        authorize(
            self._policy_adapter,
            action_type="lifecycle.archive_candidate.read",
            resource_type="archive_candidate",
            resource_id=None,
            scope=scope,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        list_items = getattr(self._repository, "list_archive_candidates", None)
        return (
            list_items(scope, status=status, severity=severity, limit=limit)
            if callable(list_items)
            else []
        )

    def dismiss_candidate(
        self, archive_candidate_id: str, actor_id: str | None, reason: str
    ) -> ArchiveCandidate:
        candidate = _require_archive(self._repository, archive_candidate_id)
        authorize(
            self._policy_adapter,
            action_type="lifecycle.archive_candidate.update",
            resource_type="archive_candidate",
            resource_id=archive_candidate_id,
            scope=candidate.owner_scope,
            trace_id=candidate.trace_id,
            actor_id=actor_id or self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="medium",
            context={"reason": reason},
        )
        return _save_archive(
            self._repository,
            candidate.model_copy(
                update={
                    "status": "dismissed",
                    "dismissed_at": datetime.now(UTC),
                    "metadata": {**candidate.metadata, "dismiss_reason": reason},
                }
            ),
        )

    def convert_to_action_proposal(
        self,
        archive_candidate_id: str,
        actor_id: str | None,
        approval_present: bool,
        reason: str,
    ) -> ArchiveCandidate:
        candidate = _require_archive(self._repository, archive_candidate_id)
        authorize(
            self._policy_adapter,
            action_type="lifecycle.archive_candidate.update",
            resource_type="archive_candidate",
            resource_id=archive_candidate_id,
            scope=candidate.owner_scope,
            trace_id=candidate.trace_id,
            actor_id=actor_id or self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="high",
            approval_present=approval_present,
            context={"conversion_only": True, "archive_executed": False},
        )
        if candidate.backup_required and not candidate.backup_verified:
            raise ValueError("backup_verification_required")
        service = _proposal_service(self._action_proposal_service, self._actor_context)
        create = getattr(service, "create_proposal", None)
        proposal = (
            create(
                ActionProposalCreateRequest(
                    trace_id=candidate.trace_id,
                    actor_id=actor_id or self._actor_context.actor_id,
                    workspace_id=self._actor_context.workspace_id,
                    source_type="generic",
                    source_id=candidate.archive_candidate_id,
                    proposal_type="generic",
                    title="Review archive candidate",
                    description=(
                        "Lifecycle archive candidate conversion. This does not execute archive."
                    ),
                    action_type="lifecycle.archive.propose",
                    target_type=candidate.resource_type,
                    target_id=candidate.resource_id,
                    owner_scope=candidate.owner_scope,
                    proposed_payload={
                        "resource_uri": candidate.resource_uri,
                        "archive_executed": False,
                    },
                    required_permissions=["lifecycle.archive_candidate.update"],
                    required_approvals=["operator"] if not approval_present else [],
                    risk_level="medium",
                    metadata={"lifecycle_candidate_type": "archive", "no_execution": True},
                    created_by=actor_id or self._actor_context.actor_id,
                )
            )
            if callable(create)
            else None
        )
        updated = candidate.model_copy(
            update={
                "status": "converted_to_action_proposal",
                "action_proposal_id": getattr(proposal, "action_proposal_id", None),
                "converted_at": datetime.now(UTC),
                "metadata": {**candidate.metadata, "archive_executed": False, "reason": reason},
            }
        )
        stored = _save_archive(self._repository, updated)
        emit_telemetry(
            self._telemetry_service,
            event_type="archive_candidate_converted",
            node_type="archive_candidate",
            node_id=stored.archive_candidate_id,
            intensity=0.8,
            trace_id=stored.trace_id,
            payload={"action_proposal_id": stored.action_proposal_id},
        )
        return stored


def _proposal_service(service: object | None, actor_context: ActorContext) -> object | None:
    with_context = getattr(service, "with_actor_context", None)
    return with_context(actor_context) if callable(with_context) else service


def _save_archive(repository: object, candidate: ArchiveCandidate) -> ArchiveCandidate:
    save = getattr(repository, "save_archive_candidate", None)
    stored = save(candidate) if callable(save) else candidate
    return stored if isinstance(stored, ArchiveCandidate) else candidate


def _require_archive(repository: object, archive_candidate_id: str) -> ArchiveCandidate:
    get = getattr(repository, "get_archive_candidate", None)
    candidate = get(archive_candidate_id) if callable(get) else None
    if not isinstance(candidate, ArchiveCandidate):
        raise ValueError("archive_candidate_not_found")
    return candidate


__all__ = ["ArchivePlanner"]
