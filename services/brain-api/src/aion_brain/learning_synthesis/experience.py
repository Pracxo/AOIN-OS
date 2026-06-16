"""Experience ledger service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.experience import (
    ExperienceCreateRequest,
    ExperienceQuery,
    ExperienceRecord,
    ExperienceType,
)
from aion_brain.contracts.learning_synthesis import ExperienceQueryResult
from aion_brain.learning_synthesis.repository import LearningSynthesisRepository
from aion_brain.outcomes._shared import (
    audit_optional,
    authorize,
    clamp_score,
    emit_telemetry,
    provenance_optional,
    scope_matches,
)
from aion_brain.outcomes.repository import OutcomeRepository


class ExperienceService:
    """Create and query generic Brain experience records."""

    def __init__(
        self,
        repository: LearningSynthesisRepository,
        policy_adapter: object,
        *,
        outcome_repository: OutcomeRepository | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._outcome_repository = outcome_repository
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service

    def create_experience(self, request: ExperienceCreateRequest) -> ExperienceRecord:
        """Create one experience record."""
        authorize(
            self._policy_adapter,
            action_type="learning.experience.create",
            resource_type="experience",
            resource_id=request.experience_id,
            scope=request.owner_scope,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            risk_level="low",
            context={
                "source_type": request.source_type,
                "experience_type": request.experience_type,
            },
        )
        now = datetime.now(UTC)
        record = ExperienceRecord(
            experience_id=request.experience_id or f"experience-{uuid4().hex}",
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            source_type=request.source_type,
            source_id=request.source_id,
            experience_type=request.experience_type,
            status="active",
            title=request.title,
            summary=request.summary,
            owner_scope=request.owner_scope,
            outcome_refs=request.outcome_refs,
            decision_refs=request.decision_refs,
            command_refs=request.command_refs,
            workflow_refs=request.workflow_refs,
            regression_refs=request.regression_refs,
            replay_refs=request.replay_refs,
            audit_refs=request.audit_refs,
            signal_refs=request.signal_refs,
            score=clamp_score(request.score),
            confidence=clamp_score(request.confidence),
            metadata={
                **request.metadata,
                "source_mutated": False,
                "automatic_action_taken": False,
            },
            observed_at=request.observed_at or now,
            created_by=request.created_by,
            created_at=now,
            updated_at=now,
        )
        stored = self._repository.save_experience(record)
        audit_optional(
            self._audit_sink,
            "experience_recorded",
            {"experience_id": stored.experience_id, "source_id": stored.source_id},
        )
        for outcome_id in stored.outcome_refs:
            provenance_optional(
                self._provenance_service,
                stored.experience_id,
                outcome_id,
                "observed_from_outcome",
            )
        emit_telemetry(
            self._telemetry_service,
            event_type="experience_recorded",
            node_type="experience",
            node_id=stored.experience_id,
            intensity=stored.score,
            trace_id=stored.trace_id,
            payload={
                "owner_scope": stored.owner_scope,
                "experience_type": stored.experience_type,
            },
        )
        return stored

    def get_experience(self, experience_id: str, scope: list[str]) -> ExperienceRecord | None:
        """Return one in-scope experience."""
        authorize(
            self._policy_adapter,
            action_type="learning.experience.read",
            resource_type="experience",
            resource_id=experience_id,
            scope=scope,
        )
        experience = self._repository.get_experience(experience_id)
        if experience is None or experience.deleted_at is not None:
            return None
        if not scope_matches(experience.owner_scope, scope):
            return None
        return experience

    def query(self, query: ExperienceQuery) -> ExperienceQueryResult:
        """Query experience records and synthesized learning material."""
        authorize(
            self._policy_adapter,
            action_type="learning.query",
            resource_type="learning",
            resource_id=None,
            scope=query.scope,
            trace_id=query.trace_id,
            risk_level="low",
        )
        experiences = self._repository.query_experiences(query)
        patterns = self._repository.list_patterns(query.scope, limit=query.limit)
        lessons = self._repository.list_lessons(query.scope, limit=query.limit)
        skill_suggestions = self._repository.list_skill_suggestions(
            query.scope,
            limit=query.limit,
        )
        regression_suggestions = self._repository.list_regression_suggestions(
            query.scope,
            limit=query.limit,
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="learning_query_completed",
            node_type="synthesis",
            node_id=query.trace_id or "learning-query",
            intensity=0.4,
            trace_id=query.trace_id,
            payload={"experience_count": len(experiences)},
        )
        return ExperienceQueryResult(
            experiences=experiences,
            patterns=patterns,
            lessons=lessons,
            skill_suggestions=skill_suggestions,
            regression_suggestions=regression_suggestions,
            total_count=len(experiences),
            constraints=[],
            metadata={"query": query.query},
        )

    def archive_experience(
        self,
        experience_id: str,
        actor_id: str | None,
        reason: str,
    ) -> ExperienceRecord:
        """Archive one experience without deleting it."""
        experience = self._repository.get_experience(experience_id)
        if experience is None:
            raise ValueError("experience_not_found")
        authorize(
            self._policy_adapter,
            action_type="learning.experience.update",
            resource_type="experience",
            resource_id=experience_id,
            scope=experience.owner_scope,
            actor_id=actor_id,
            trace_id=experience.trace_id,
            risk_level="low",
            context={"reason": reason},
        )
        archived = experience.model_copy(
            update={
                "status": "archived",
                "archived_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "metadata": {**experience.metadata, "archive_reason": reason},
            }
        )
        return self._repository.save_experience(archived)

    def soft_delete_experience(
        self,
        experience_id: str,
        actor_id: str | None,
        reason: str,
    ) -> bool:
        """Soft-delete one experience."""
        experience = self._repository.get_experience(experience_id)
        if experience is None:
            return False
        authorize(
            self._policy_adapter,
            action_type="learning.experience.delete",
            resource_type="experience",
            resource_id=experience_id,
            scope=experience.owner_scope,
            actor_id=actor_id,
            risk_level="medium",
            context={"reason": reason},
        )
        deleted = experience.model_copy(
            update={
                "deleted_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "metadata": {**experience.metadata, "delete_reason": reason},
            }
        )
        self._repository.save_experience(deleted)
        return True

    def create_from_outcome(
        self,
        outcome_id: str,
        scope: list[str],
    ) -> ExperienceRecord | None:
        """Create an experience from an outcome if one does not already exist."""
        if self._outcome_repository is None:
            return None
        existing = self._repository.get_experience_by_source("outcome", outcome_id)
        if existing is not None:
            return existing
        outcome = self._outcome_repository.get_outcome(outcome_id)
        if outcome is None or not scope_matches(outcome.owner_scope, scope):
            return None
        experience_type, score = _experience_type_score(outcome.status)
        return self.create_experience(
            ExperienceCreateRequest(
                trace_id=outcome.trace_id,
                actor_id=outcome.actor_id,
                workspace_id=outcome.workspace_id,
                source_type="outcome",
                source_id=outcome.outcome_id,
                experience_type=experience_type,
                title=f"Outcome {outcome.status}",
                summary=outcome.summary,
                owner_scope=outcome.owner_scope,
                outcome_refs=[outcome.outcome_id],
                decision_refs=outcome.decision_refs,
                command_refs=[outcome.source_id] if outcome.source_type == "command" else [],
                workflow_refs=[outcome.source_id] if outcome.source_type == "workflow" else [],
                score=score,
                confidence=outcome.confidence,
                metadata={"outcome_status": outcome.status},
                observed_at=outcome.observed_at,
                created_by=outcome.created_by,
            )
        )

    def create_from_feedback(
        self,
        outcome_feedback_id: str,
        scope: list[str],
    ) -> ExperienceRecord | None:
        """Create an experience from outcome feedback."""
        if self._outcome_repository is None:
            return None
        existing = self._repository.get_experience_by_source(
            "outcome",
            outcome_feedback_id,
        )
        if existing is not None:
            return existing
        feedback = self._outcome_repository.get_feedback(outcome_feedback_id)
        if feedback is None:
            return None
        outcome_refs = [feedback.outcome_id] if feedback.outcome_id else []
        outcome = (
            self._outcome_repository.get_outcome(feedback.outcome_id)
            if feedback.outcome_id
            else None
        )
        owner_scope = outcome.owner_scope if outcome is not None else scope
        if not scope_matches(owner_scope, scope):
            return None
        experience_type, score = _feedback_experience_type_score(feedback.feedback_type)
        return self.create_experience(
            ExperienceCreateRequest(
                trace_id=feedback.trace_id,
                source_type="outcome",
                source_id=feedback.outcome_feedback_id,
                experience_type=experience_type,
                title=f"Outcome feedback {feedback.feedback_type}",
                summary=feedback.message,
                owner_scope=owner_scope,
                outcome_refs=outcome_refs,
                score=score,
                confidence=0.75,
                metadata={"feedback_type": feedback.feedback_type, "severity": feedback.severity},
                observed_at=feedback.created_at,
                created_by=feedback.created_by,
            )
        )


def _experience_type_score(status: str) -> tuple[ExperienceType, float]:
    if status == "verified":
        return "success", 0.9
    if status == "partial":
        return "partial_success", 0.55
    if status == "failed":
        return "failure", 0.2
    if status == "contradicted":
        return "contradiction", 0.25
    if status == "unknown":
        return "generic", 0.5
    return "generic", 0.5


def _feedback_experience_type_score(feedback_type: str) -> tuple[ExperienceType, float]:
    mapping: dict[str, tuple[ExperienceType, float]] = {
        "success_pattern": ("success", 0.85),
        "failure_pattern": ("failure", 0.25),
        "partial_success": ("partial_success", 0.55),
        "unexpected_effect": ("unexpected_effect", 0.4),
        "missing_effect": ("missing_effect", 0.35),
        "contradiction": ("contradiction", 0.25),
        "regression_candidate": ("regression_drift", 0.3),
    }
    return mapping.get(feedback_type, ("generic", 0.5))


__all__ = ["ExperienceService"]
