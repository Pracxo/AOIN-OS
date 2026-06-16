"""Shared helpers for learning synthesis tests."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from aion_brain.contracts.experience import ExperienceCreateRequest
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.learning_synthesis.experience import ExperienceService
from aion_brain.learning_synthesis.lessons import LessonService
from aion_brain.learning_synthesis.miner import PatternMiner
from aion_brain.learning_synthesis.query import LearningQueryService
from aion_brain.learning_synthesis.regression_suggestions import RegressionSuggestionService
from aion_brain.learning_synthesis.repository import LearningSynthesisRepository
from aion_brain.learning_synthesis.skill_suggestions import SkillSuggestionService
from aion_brain.learning_synthesis.synthesizer import LearningSynthesizer
from aion_brain.outcomes.repository import OutcomeRepository


class AllowPolicy:
    def __init__(self) -> None:
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=True,
            approval_required=False,
            reason="allowed",
            constraints=[],
            audit_level="standard",
        )


class DenyPolicy:
    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=False,
            approval_required=False,
            reason="denied",
            constraints=[],
            audit_level="standard",
        )


class TelemetrySink:
    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


class Settings:
    learning_min_pattern_frequency = 2
    learning_min_pattern_confidence = 0.5


class LearningBundle:
    def __init__(self, policy: object | None = None) -> None:
        self.repository = LearningSynthesisRepository()
        self.outcome_repository = OutcomeRepository()
        self.policy = policy or AllowPolicy()
        self.telemetry = TelemetrySink()
        self.experiences = ExperienceService(
            self.repository,
            self.policy,
            outcome_repository=self.outcome_repository,
            telemetry_service=self.telemetry,
        )
        self.miner = PatternMiner(
            self.repository,
            self.policy,
            telemetry_service=self.telemetry,
        )
        self.lessons = LessonService(
            self.repository,
            self.policy,
            telemetry_service=self.telemetry,
        )
        self.skill_suggestions = SkillSuggestionService(
            self.repository,
            self.policy,
            telemetry_service=self.telemetry,
        )
        self.regression_suggestions = RegressionSuggestionService(
            self.repository,
            self.policy,
            telemetry_service=self.telemetry,
        )
        self.query = LearningQueryService(self.experiences)
        self.synthesizer = LearningSynthesizer(
            self.repository,
            self.policy,
            experience_service=self.experiences,
            pattern_miner=self.miner,
            lesson_service=self.lessons,
            skill_suggestion_service=self.skill_suggestions,
            regression_suggestion_service=self.regression_suggestions,
            outcome_repository=self.outcome_repository,
            telemetry_service=self.telemetry,
            settings=Settings(),
        )


def bundle(policy: object | None = None) -> LearningBundle:
    return LearningBundle(policy)


def create_experience_request(
    source_id: str,
    *,
    experience_type: str = "failure",
    summary: str = "Generic repeated failure",
    score: float = 0.2,
    confidence: float = 0.8,
) -> ExperienceCreateRequest:
    return ExperienceCreateRequest(
        trace_id="trace-learning",
        source_type="generic",
        source_id=source_id,
        experience_type=cast(Any, experience_type),
        title=f"Experience {source_id}",
        summary=summary,
        owner_scope=["workspace:main"],
        score=score,
        confidence=confidence,
        observed_at=datetime.now(UTC),
    )
