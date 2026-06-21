"""Redaction candidate planner."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.action_proposals import ActionProposalCreateRequest
from aion_brain.contracts.lifecycle import LifecycleSeverity, RedactionCandidate
from aion_brain.contracts.resource_registry import ResourceDescriptor
from aion_brain.contracts.retention import RetentionClassification
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.lifecycle.redaction import sensitive_metadata_paths


class RedactionPlanner:
    """Create redaction candidates without executing redaction."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        action_proposal_service: object | None = None,
        telemetry_service: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._action_proposal_service = action_proposal_service
        self._telemetry_service = telemetry_service
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> RedactionPlanner:
        return RedactionPlanner(
            self._repository,
            self._policy_adapter,
            action_proposal_service=self._action_proposal_service,
            telemetry_service=self._telemetry_service,
            actor_context=actor_context,
        )

    def create_candidate(
        self,
        resource: ResourceDescriptor,
        classification: RetentionClassification,
        reason: str,
        sensitive_paths: list[str] | None = None,
        *,
        persist: bool = True,
    ) -> RedactionCandidate:
        authorize(
            self._policy_adapter,
            action_type="lifecycle.redaction_candidate.create",
            resource_type="redaction_candidate",
            resource_id=resource.resource_uri,
            scope=resource.owner_scope,
            trace_id=resource.trace_id or self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=resource.workspace_id or self._actor_context.workspace_id,
            risk_level="medium",
            context={"redaction_executed": False},
        )
        paths = (
            sensitive_paths
            if sensitive_paths is not None
            else sensitive_metadata_paths(resource.metadata)
        )
        severity: LifecycleSeverity = (
            "high" if resource.sensitivity in {"confidential", "restricted"} else "medium"
        )
        candidate = RedactionCandidate(
            redaction_candidate_id=f"redaction-candidate-{uuid4().hex}",
            trace_id=resource.trace_id or self._actor_context.trace_id,
            resource_uri=resource.resource_uri,
            resource_type=resource.resource_type,
            resource_id=resource.resource_id,
            source_system=resource.source_system,
            status="proposed",
            severity=severity,
            reason=reason,
            sensitive_paths=paths,
            suggested_redaction_mode="redact_sensitive" if paths else "manual_review",
            classification_id=classification.classification_id,
            owner_scope=resource.owner_scope,
            metadata={"redaction_executed": False, "source_records_mutated": False},
            created_by=self._actor_context.actor_id,
            created_at=datetime.now(UTC),
        )
        stored = _save_redaction(self._repository, candidate) if persist else candidate
        emit_telemetry(
            self._telemetry_service,
            event_type="redaction_candidate_created",
            node_type="redaction_candidate",
            node_id=stored.redaction_candidate_id,
            intensity=1.0 if stored.severity in {"high", "critical"} else 0.7,
            trace_id=stored.trace_id,
            payload={"resource_uri": stored.resource_uri, "severity": stored.severity},
        )
        return stored

    def list_candidates(
        self,
        scope: list[str],
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[RedactionCandidate]:
        authorize(
            self._policy_adapter,
            action_type="lifecycle.redaction_candidate.read",
            resource_type="redaction_candidate",
            resource_id=None,
            scope=scope,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        list_items = getattr(self._repository, "list_redaction_candidates", None)
        return (
            list_items(scope, status=status, severity=severity, limit=limit)
            if callable(list_items)
            else []
        )

    def dismiss_candidate(
        self, redaction_candidate_id: str, actor_id: str | None, reason: str
    ) -> RedactionCandidate:
        candidate = _require_redaction(self._repository, redaction_candidate_id)
        authorize(
            self._policy_adapter,
            action_type="lifecycle.redaction_candidate.update",
            resource_type="redaction_candidate",
            resource_id=redaction_candidate_id,
            scope=candidate.owner_scope,
            trace_id=candidate.trace_id,
            actor_id=actor_id or self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="medium",
            context={"reason": reason},
        )
        return _save_redaction(
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
        redaction_candidate_id: str,
        actor_id: str | None,
        approval_present: bool,
        reason: str,
    ) -> RedactionCandidate:
        candidate = _require_redaction(self._repository, redaction_candidate_id)
        authorize(
            self._policy_adapter,
            action_type="lifecycle.redaction_candidate.update",
            resource_type="redaction_candidate",
            resource_id=redaction_candidate_id,
            scope=candidate.owner_scope,
            trace_id=candidate.trace_id,
            actor_id=actor_id or self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="high",
            approval_present=approval_present,
            context={"conversion_only": True, "redaction_executed": False},
        )
        service = _proposal_service(self._action_proposal_service, self._actor_context)
        create = getattr(service, "create_proposal", None)
        proposal = (
            create(
                ActionProposalCreateRequest(
                    trace_id=candidate.trace_id,
                    actor_id=actor_id or self._actor_context.actor_id,
                    workspace_id=self._actor_context.workspace_id,
                    source_type="generic",
                    source_id=candidate.redaction_candidate_id,
                    proposal_type="generic",
                    title="Review redaction candidate",
                    description=(
                        "Lifecycle redaction candidate conversion. This does not execute redaction."
                    ),
                    action_type="lifecycle.redaction.propose",
                    target_type=candidate.resource_type,
                    target_id=candidate.resource_id,
                    owner_scope=candidate.owner_scope,
                    proposed_payload={
                        "resource_uri": candidate.resource_uri,
                        "sensitive_paths": candidate.sensitive_paths,
                        "redaction_executed": False,
                    },
                    required_permissions=["lifecycle.redaction_candidate.update"],
                    required_approvals=["operator"] if not approval_present else [],
                    risk_level="high" if candidate.severity in {"high", "critical"} else "medium",
                    metadata={"lifecycle_candidate_type": "redaction", "no_execution": True},
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
                "metadata": {**candidate.metadata, "redaction_executed": False, "reason": reason},
            }
        )
        stored = _save_redaction(self._repository, updated)
        emit_telemetry(
            self._telemetry_service,
            event_type="redaction_candidate_converted",
            node_type="redaction_candidate",
            node_id=stored.redaction_candidate_id,
            intensity=0.9,
            trace_id=stored.trace_id,
            payload={"action_proposal_id": stored.action_proposal_id},
        )
        return stored


def _proposal_service(service: object | None, actor_context: ActorContext) -> object | None:
    with_context = getattr(service, "with_actor_context", None)
    return with_context(actor_context) if callable(with_context) else service


def _save_redaction(repository: object, candidate: RedactionCandidate) -> RedactionCandidate:
    save = getattr(repository, "save_redaction_candidate", None)
    stored = save(candidate) if callable(save) else candidate
    return stored if isinstance(stored, RedactionCandidate) else candidate


def _require_redaction(repository: object, redaction_candidate_id: str) -> RedactionCandidate:
    get = getattr(repository, "get_redaction_candidate", None)
    candidate = get(redaction_candidate_id) if callable(get) else None
    if not isinstance(candidate, RedactionCandidate):
        raise ValueError("redaction_candidate_not_found")
    return candidate


__all__ = ["RedactionPlanner"]
