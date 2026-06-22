"""Lesson record service for learning synthesis."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.learning_synthesis import (
    LearningPattern,
    LessonRecord,
    LessonType,
)
from aion_brain.learning_synthesis.repository import LearningSynthesisRepository
from aion_brain.outcomes._shared import audit_optional, authorize, emit_telemetry

_LESSON_TEXT = {
    "repeated_success": (
        "Repeated success pattern observed. Preserve the conditions that produced this outcome."
    ),
    "repeated_failure": (
        "Repeated failure pattern observed. Review planning, context, policy, "
        "and verification before repeating."
    ),
    "missing_effect": (
        "Expected effects were missing. Add clearer success criteria or stronger "
        "verification before execution."
    ),
    "unexpected_effect": (
        "Unexpected effects were observed. Review assumptions and counterfactuals before repeating."
    ),
    "approval_bottleneck": (
        "Approval bottleneck observed. Review risk level, approval scope, and autonomy constraints."
    ),
    "regression_drift": (
        "Regression drift observed. Add or update regression cases before changing this path."
    ),
    "replay_drift": (
        "Replay drift observed. Review deterministic replay inputs and expected snapshots."
    ),
    "contradiction": (
        "Contradiction pattern observed. Review belief, evidence, and memory governance state."
    ),
    "generic": "Generic learning pattern observed. Review linked experiences and outcomes.",
}


class LessonService:
    """Create and query deterministic lesson records."""

    def __init__(
        self,
        repository: LearningSynthesisRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink

    def build_lesson_from_pattern(
        self,
        pattern: LearningPattern,
        created_by: str | None,
    ) -> LessonRecord:
        """Build but do not persist one deterministic lesson."""
        lesson_type = _lesson_type(pattern.pattern_type)
        return LessonRecord(
            lesson_id=f"lesson-{uuid4().hex}",
            trace_id=pattern.trace_id,
            lesson_type=lesson_type,
            status="active",
            title=f"{pattern.pattern_type.replace('_', ' ').title()} Lesson",
            lesson=_LESSON_TEXT.get(pattern.pattern_type, _LESSON_TEXT["generic"]),
            owner_scope=pattern.owner_scope,
            pattern_refs=[pattern.pattern_id],
            experience_refs=pattern.experience_refs,
            outcome_refs=pattern.outcome_refs,
            evidence_refs=pattern.evidence_refs,
            confidence=pattern.confidence,
            applicability={
                "pattern_type": pattern.pattern_type,
                "frequency": pattern.frequency,
                "generic": True,
            },
            constraints=[
                "no_auto_promotion",
                "no_code_modification",
                "review_required",
            ],
            metadata={"source": "pattern", "no_skill_promotion": True},
            created_by=created_by,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    def create_lesson_from_pattern(
        self,
        pattern: LearningPattern,
        created_by: str | None,
    ) -> LessonRecord:
        """Create a lesson from a pattern."""
        return self.create_lesson(self.build_lesson_from_pattern(pattern, created_by))

    def create_lesson(self, lesson: LessonRecord) -> LessonRecord:
        """Persist one lesson."""
        authorize(
            self._policy_adapter,
            action_type="learning.lesson.create",
            resource_type="lesson",
            resource_id=lesson.lesson_id,
            scope=lesson.owner_scope,
            trace_id=lesson.trace_id,
            risk_level="low",
            context={"lesson_type": lesson.lesson_type},
        )
        stored = self._repository.save_lesson(
            lesson.model_copy(
                update={
                    "created_at": lesson.created_at or datetime.now(UTC),
                    "updated_at": datetime.now(UTC),
                }
            )
        )
        audit_optional(
            self._audit_sink,
            "lesson_created",
            {"lesson_id": stored.lesson_id, "lesson_type": stored.lesson_type},
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="lesson_created",
            node_type="lesson",
            node_id=stored.lesson_id,
            intensity=stored.confidence,
            trace_id=stored.trace_id,
            payload={"lesson_type": stored.lesson_type},
        )
        return stored

    def list_lessons(
        self,
        scope: list[str],
        lesson_type: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[LessonRecord]:
        """List lessons in scope."""
        authorize(
            self._policy_adapter,
            action_type="learning.lesson.read",
            resource_type="lesson",
            resource_id=None,
            scope=scope,
            risk_level="low",
        )
        return self._repository.list_lessons(
            scope,
            lesson_type=lesson_type,
            status=status,
            limit=limit,
        )

    def archive_lesson(
        self,
        lesson_id: str,
        actor_id: str | None,
        reason: str,
    ) -> LessonRecord:
        """Archive one lesson."""
        lesson = self._repository.get_lesson(lesson_id)
        if lesson is None:
            raise ValueError("lesson_not_found")
        authorize(
            self._policy_adapter,
            action_type="learning.lesson.update",
            resource_type="lesson",
            resource_id=lesson_id,
            scope=lesson.owner_scope,
            actor_id=actor_id,
            risk_level="low",
            context={"reason": reason},
        )
        return self._repository.save_lesson(
            lesson.model_copy(
                update={
                    "status": "archived",
                    "archived_at": datetime.now(UTC),
                    "updated_at": datetime.now(UTC),
                    "metadata": {**lesson.metadata, "archive_reason": reason},
                }
            )
        )


def _lesson_type(pattern_type: str) -> LessonType:
    if pattern_type == "approval_bottleneck":
        return "approval"
    if pattern_type in {"regression_drift", "replay_drift"}:
        return "regression"
    if pattern_type in {"repeated_failure", "recovery_pattern"}:
        return "planning"
    if pattern_type == "missing_context":
        return "contextual"
    if pattern_type in {"missing_effect", "unexpected_effect"}:
        return "execution"
    if pattern_type == "contradiction":
        return "memory"
    return "generic"


__all__ = ["LessonService"]
