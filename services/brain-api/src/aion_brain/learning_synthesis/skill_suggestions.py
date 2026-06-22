"""Skill candidate suggestion service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.learning_synthesis import (
    LearningPattern,
    LearningSeverity,
    LessonRecord,
    ProposedSkillType,
    SkillCandidateSuggestion,
)
from aion_brain.learning_synthesis.repository import LearningSynthesisRepository
from aion_brain.outcomes._shared import audit_optional, authorize, emit_telemetry


class SkillSuggestionService:
    """Create reviewable skill candidate suggestions without promotion."""

    def __init__(
        self,
        repository: LearningSynthesisRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        skill_service: object | None = None,
        settings: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._skill_service = skill_service
        self._settings = settings

    def build_suggestion_from_pattern(
        self,
        pattern: LearningPattern,
        lesson: LessonRecord | None,
        created_by: str | None,
    ) -> SkillCandidateSuggestion:
        """Build but do not persist one skill suggestion."""
        risk_level: LearningSeverity = "high" if pattern.severity in {"high", "critical"} else "low"
        return SkillCandidateSuggestion(
            suggestion_id=f"skill-suggestion-{uuid4().hex}",
            trace_id=pattern.trace_id,
            pattern_id=pattern.pattern_id,
            lesson_id=lesson.lesson_id if lesson else None,
            status="suggested",
            title=f"Review {pattern.pattern_type.replace('_', ' ')} procedure",
            description=(
                "A reusable generic procedure may be worth reviewing. This is a suggestion only."
            ),
            owner_scope=pattern.owner_scope,
            proposed_skill_type=_skill_type(pattern.pattern_type),
            source_refs=[pattern.pattern_id] + ([lesson.lesson_id] if lesson else []),
            risk_level=risk_level,
            confidence=pattern.confidence,
            promotion_allowed=False,
            metadata={
                "auto_promotion": False,
                "skill_record_created": False,
                "pattern_type": pattern.pattern_type,
            },
            created_by=created_by,
            created_at=datetime.now(UTC),
        )

    def create_suggestion_from_pattern(
        self,
        pattern: LearningPattern,
        lesson: LessonRecord | None,
        created_by: str | None,
    ) -> SkillCandidateSuggestion:
        """Create one skill suggestion from a pattern."""
        return self.create_suggestion(
            self.build_suggestion_from_pattern(pattern, lesson, created_by)
        )

    def create_suggestion(self, suggestion: SkillCandidateSuggestion) -> SkillCandidateSuggestion:
        """Persist one skill suggestion."""
        authorize(
            self._policy_adapter,
            action_type="learning.skill_suggestion.create",
            resource_type="skill_suggestion",
            resource_id=suggestion.suggestion_id,
            scope=suggestion.owner_scope,
            trace_id=suggestion.trace_id,
            risk_level="low",
            context={"promotion_allowed": False},
        )
        stored = self._repository.save_skill_suggestion(
            suggestion.model_copy(update={"created_at": suggestion.created_at or datetime.now(UTC)})
        )
        audit_optional(
            self._audit_sink,
            "skill_candidate_suggestion_created",
            {"suggestion_id": stored.suggestion_id},
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="skill_candidate_suggestion_created",
            node_type="skill_suggestion",
            node_id=stored.suggestion_id,
            intensity=stored.confidence,
            trace_id=stored.trace_id,
            payload={"risk_level": stored.risk_level},
        )
        return stored

    def list_suggestions(
        self,
        scope: list[str],
        status: str | None = None,
        limit: int = 100,
    ) -> list[SkillCandidateSuggestion]:
        """List skill suggestions in scope."""
        authorize(
            self._policy_adapter,
            action_type="learning.skill_suggestion.read",
            resource_type="skill_suggestion",
            resource_id=None,
            scope=scope,
            risk_level="low",
        )
        return self._repository.list_skill_suggestions(scope, status=status, limit=limit)

    def accept_suggestion(
        self,
        suggestion_id: str,
        actor_id: str | None,
        reason: str,
    ) -> SkillCandidateSuggestion:
        """Accept a suggestion without creating a skill."""
        return self._update_status(suggestion_id, "accepted", actor_id, reason)

    def reject_suggestion(
        self,
        suggestion_id: str,
        actor_id: str | None,
        reason: str,
    ) -> SkillCandidateSuggestion:
        """Reject a suggestion without creating a skill."""
        return self._update_status(suggestion_id, "rejected", actor_id, reason)

    def convert_to_skill_candidate(
        self,
        suggestion_id: str,
        actor_id: str | None,
        approval_present: bool,
        reason: str,
    ) -> SkillCandidateSuggestion:
        """Convert to a passive skill candidate reference when explicitly allowed."""
        suggestion = self._get_required(suggestion_id)
        if suggestion.risk_level in {"high", "critical"} and not approval_present:
            raise PermissionError("approval_required")
        authorize(
            self._policy_adapter,
            action_type="learning.skill_suggestion.convert",
            resource_type="skill_suggestion",
            resource_id=suggestion_id,
            scope=suggestion.owner_scope,
            actor_id=actor_id,
            trace_id=suggestion.trace_id,
            risk_level=suggestion.risk_level,
            approval_present=approval_present,
            context={"reason": reason, "skill_promotion": False},
        )
        candidate_id = f"skill-candidate-{uuid4().hex}"
        updated = suggestion.model_copy(
            update={
                "status": "converted",
                "skill_candidate_id": candidate_id,
                "resolved_at": datetime.now(UTC),
                "metadata": {
                    **suggestion.metadata,
                    "convert_reason": reason,
                    "skill_record_created": False,
                    "skill_activated": False,
                },
            }
        )
        stored = self._repository.save_skill_suggestion(updated)
        emit_telemetry(
            self._telemetry_service,
            event_type="skill_candidate_suggestion_converted",
            node_type="skill_suggestion",
            node_id=stored.suggestion_id,
            intensity=stored.confidence,
            trace_id=stored.trace_id,
            payload={"skill_candidate_id": candidate_id, "skill_record_created": False},
        )
        return stored

    def _update_status(
        self,
        suggestion_id: str,
        status: str,
        actor_id: str | None,
        reason: str,
    ) -> SkillCandidateSuggestion:
        suggestion = self._get_required(suggestion_id)
        authorize(
            self._policy_adapter,
            action_type="learning.skill_suggestion.update",
            resource_type="skill_suggestion",
            resource_id=suggestion_id,
            scope=suggestion.owner_scope,
            actor_id=actor_id,
            risk_level="low",
            context={"status": status, "reason": reason},
        )
        return self._repository.save_skill_suggestion(
            suggestion.model_copy(
                update={
                    "status": status,
                    "resolved_at": datetime.now(UTC),
                    "metadata": {**suggestion.metadata, "resolution_reason": reason},
                }
            )
        )

    def _get_required(self, suggestion_id: str) -> SkillCandidateSuggestion:
        suggestion = self._repository.get_skill_suggestion(suggestion_id)
        if suggestion is None:
            raise ValueError("skill_suggestion_not_found")
        return suggestion


def _skill_type(pattern_type: str) -> ProposedSkillType:
    if pattern_type in {"missing_context", "missing_effect"}:
        return "retrieval"
    if pattern_type in {"repeated_failure", "recovery_pattern"}:
        return "planning"
    if pattern_type in {"unexpected_effect", "repeated_success"}:
        return "procedural"
    if pattern_type == "approval_bottleneck":
        return "operator"
    return "generic"


__all__ = ["SkillSuggestionService"]
