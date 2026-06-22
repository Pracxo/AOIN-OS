"""Learning synthesis coordinator."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.experience import ExperienceRecord, ExperienceType
from aion_brain.contracts.learning_synthesis import (
    LearningPattern,
    LearningPatternType,
    LearningSynthesisRequest,
    LearningSynthesisRun,
    LearningSynthesisStatus,
    LessonRecord,
    PatternMiningRequest,
    RegressionCandidateSuggestion,
    SkillCandidateSuggestion,
)
from aion_brain.contracts.outcomes import OutcomeRecord
from aion_brain.learning_synthesis.experience import ExperienceService
from aion_brain.learning_synthesis.lessons import LessonService
from aion_brain.learning_synthesis.miner import PatternMiner
from aion_brain.learning_synthesis.patterns import (
    normalized_summary_key,
    pattern_type_for,
    recommendation_for,
    severity_for_pattern,
)
from aion_brain.learning_synthesis.regression_suggestions import (
    RegressionSuggestionService,
)
from aion_brain.learning_synthesis.repository import LearningSynthesisRepository
from aion_brain.learning_synthesis.skill_suggestions import SkillSuggestionService
from aion_brain.outcomes._shared import audit_optional, authorize, clamp_score, emit_telemetry
from aion_brain.outcomes.repository import OutcomeRepository


class LearningSynthesizer:
    """Turn outcomes and experiences into reviewable learning material."""

    def __init__(
        self,
        repository: LearningSynthesisRepository,
        policy_adapter: object,
        *,
        experience_service: ExperienceService,
        pattern_miner: PatternMiner,
        lesson_service: LessonService,
        skill_suggestion_service: SkillSuggestionService,
        regression_suggestion_service: RegressionSuggestionService,
        outcome_repository: OutcomeRepository | None = None,
        autonomy_governor: object | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        settings: object | None = None,
        preference_learning_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._experience_service = experience_service
        self._pattern_miner = pattern_miner
        self._lesson_service = lesson_service
        self._skill_suggestion_service = skill_suggestion_service
        self._regression_suggestion_service = regression_suggestion_service
        self._outcome_repository = outcome_repository
        self._autonomy_governor = autonomy_governor
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._settings = settings
        self._preference_learning_service = preference_learning_service

    def synthesize(self, request: LearningSynthesisRequest) -> LearningSynthesisRun:
        """Run deterministic learning synthesis."""
        run_id = request.synthesis_run_id or f"learning-synthesis-{uuid4().hex}"
        authorize(
            self._policy_adapter,
            action_type="learning.synthesize",
            resource_type="learning_synthesis",
            resource_id=run_id,
            scope=request.owner_scope,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            risk_level="medium" if request.mode == "controlled" else "low",
            context={"mode": request.mode, "no_skill_promotion": True},
        )
        if not _autonomy_allows(self._autonomy_governor, request):
            return self._blocked_run(run_id, request, "blocked_by_autonomy")
        emit_telemetry(
            self._telemetry_service,
            event_type="learning_synthesis_started",
            node_type="synthesis",
            node_id=run_id,
            intensity=0.5,
            trace_id=request.trace_id,
            payload={"mode": request.mode},
        )
        experiences = self._load_or_create_experiences(request)
        patterns = self._load_or_mine_patterns(request, experiences)
        lessons = self._create_lessons(request, patterns)
        skill_suggestions = self._create_skill_suggestions(request, patterns, lessons)
        regression_suggestions = self._create_regression_suggestions(request, patterns)
        reflection_candidate_ids = (
            [f"reflection-candidate-{uuid4().hex}" for _ in lessons]
            if request.create_reflection_candidates
            else []
        )
        now = datetime.now(UTC)
        run = LearningSynthesisRun(
            synthesis_run_id=run_id,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            status="dry_run" if request.mode == "dry_run" else "completed",
            mode=request.mode,
            owner_scope=request.owner_scope,
            input_refs=_input_refs(request),
            experiences=experiences,
            patterns=patterns,
            lessons=lessons,
            reflection_candidate_ids=reflection_candidate_ids,
            skill_candidate_suggestions=skill_suggestions,
            regression_candidate_suggestions=regression_suggestions,
            result={
                "skill_promoted": False,
                "code_modified": False,
                "external_calls": False,
                "source_records_mutated": False,
                "memory_candidate_created": bool(
                    request.metadata.get("create_memory_candidate", False)
                )
                and request.mode == "controlled",
            },
            warnings=[],
            created_by=request.created_by,
            created_at=now,
            completed_at=now,
        )
        stored = self._repository.save_synthesis_run(run)
        self._preference_candidate_if_requested(request, stored)
        audit_optional(
            self._audit_sink,
            "learning_synthesis_completed",
            {"synthesis_run_id": stored.synthesis_run_id, "mode": stored.mode},
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="learning_synthesis_completed",
            node_type="synthesis",
            node_id=stored.synthesis_run_id,
            intensity=0.8 if stored.status in {"completed", "dry_run"} else 1.0,
            trace_id=stored.trace_id,
            payload={"lesson_count": len(stored.lessons), "mode": stored.mode},
        )
        return stored

    def _preference_candidate_if_requested(
        self,
        request: LearningSynthesisRequest,
        run: LearningSynthesisRun,
    ) -> None:
        if request.metadata.get("create_preference_candidate") is not True:
            return
        propose = getattr(self._preference_learning_service, "propose_from_feedback", None)
        if not callable(propose):
            return
        try:
            propose(
                {
                    **request.metadata,
                    "trace_id": run.trace_id,
                    "actor_id": run.actor_id,
                    "workspace_id": run.workspace_id,
                    "feedback_id": run.synthesis_run_id,
                    "preference_key": request.metadata.get(
                        "preference_key",
                        "interaction.learning_feedback",
                    ),
                },
                explicit=True,
                owner_scope=run.owner_scope,
            )
        except Exception:
            return

    def get(self, synthesis_run_id: str) -> LearningSynthesisRun | None:
        """Return one synthesis run."""
        return self._repository.get_synthesis_run(synthesis_run_id)

    def _load_or_create_experiences(
        self,
        request: LearningSynthesisRequest,
    ) -> list[ExperienceRecord]:
        experiences = [
            item
            for experience_id in request.experience_ids
            if (item := self._repository.get_experience(experience_id)) is not None
        ]
        if self._outcome_repository is None:
            return experiences
        for outcome_id in request.outcome_ids:
            if request.mode == "controlled":
                experience = self._experience_service.create_from_outcome(
                    outcome_id,
                    request.owner_scope,
                )
            else:
                outcome = self._outcome_repository.get_outcome(outcome_id)
                experience = (
                    _experience_from_outcome(outcome, request.owner_scope, request.created_by)
                    if outcome is not None
                    else None
                )
            if experience is not None:
                experiences.append(experience)
        return _dedupe_experiences(experiences)

    def _load_or_mine_patterns(
        self,
        request: LearningSynthesisRequest,
        experiences: list[ExperienceRecord],
    ) -> list[LearningPattern]:
        if request.pattern_ids:
            return [
                item
                for pattern_id in request.pattern_ids
                if (item := self._repository.get_pattern(pattern_id)) is not None
            ]
        if request.mode == "controlled":
            run = self._pattern_miner.mine(
                PatternMiningRequest(
                    trace_id=request.trace_id,
                    actor_id=request.actor_id,
                    workspace_id=request.workspace_id,
                    owner_scope=request.owner_scope,
                    experience_ids=[item.experience_id for item in experiences],
                    min_frequency=getattr(self._settings, "learning_min_pattern_frequency", 2),
                    min_confidence=getattr(
                        self._settings,
                        "learning_min_pattern_confidence",
                        0.6,
                    ),
                    dry_run=False,
                    created_by=request.created_by,
                )
            )
            return run.patterns
        return _patterns_from_experiences(request, experiences)

    def _create_lessons(
        self,
        request: LearningSynthesisRequest,
        patterns: list[LearningPattern],
    ) -> list[LessonRecord]:
        if not request.create_lessons:
            return []
        if request.mode == "controlled":
            return [
                self._lesson_service.create_lesson_from_pattern(pattern, request.created_by)
                for pattern in patterns
            ]
        return [
            self._lesson_service.build_lesson_from_pattern(pattern, request.created_by)
            for pattern in patterns
        ]

    def _create_skill_suggestions(
        self,
        request: LearningSynthesisRequest,
        patterns: list[LearningPattern],
        lessons: list[LessonRecord],
    ) -> list[SkillCandidateSuggestion]:
        if not request.create_skill_suggestions:
            return []
        lesson_by_pattern = {
            lesson.pattern_refs[0]: lesson for lesson in lessons if lesson.pattern_refs
        }
        if request.mode == "controlled":
            return [
                self._skill_suggestion_service.create_suggestion_from_pattern(
                    pattern,
                    lesson_by_pattern.get(pattern.pattern_id),
                    request.created_by,
                )
                for pattern in patterns
            ]
        return [
            self._skill_suggestion_service.build_suggestion_from_pattern(
                pattern,
                lesson_by_pattern.get(pattern.pattern_id),
                request.created_by,
            )
            for pattern in patterns
        ]

    def _create_regression_suggestions(
        self,
        request: LearningSynthesisRequest,
        patterns: list[LearningPattern],
    ) -> list[RegressionCandidateSuggestion]:
        if not request.create_regression_suggestions:
            return []
        failure_patterns = [
            pattern
            for pattern in patterns
            if pattern.pattern_type in {"repeated_failure", "regression_drift", "replay_drift"}
        ]
        if request.mode == "controlled":
            return [
                self._regression_suggestion_service.create_suggestion_from_failure(
                    pattern,
                    pattern.outcome_refs[0] if pattern.outcome_refs else None,
                    request.created_by,
                )
                for pattern in failure_patterns
            ]
        return [
            self._regression_suggestion_service.build_suggestion_from_failure(
                pattern,
                pattern.outcome_refs[0] if pattern.outcome_refs else None,
                request.created_by,
            )
            for pattern in failure_patterns
        ]

    def _blocked_run(
        self,
        run_id: str,
        request: LearningSynthesisRequest,
        status: LearningSynthesisStatus,
    ) -> LearningSynthesisRun:
        now = datetime.now(UTC)
        return self._repository.save_synthesis_run(
            LearningSynthesisRun(
                synthesis_run_id=run_id,
                trace_id=request.trace_id,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                status=status,
                mode=request.mode,
                owner_scope=request.owner_scope,
                input_refs=_input_refs(request),
                experiences=[],
                patterns=[],
                lessons=[],
                reflection_candidate_ids=[],
                skill_candidate_suggestions=[],
                regression_candidate_suggestions=[],
                result={"blocked": True, "skill_promoted": False},
                warnings=[{"reason": status}],
                created_by=request.created_by,
                created_at=now,
                completed_at=now,
            )
        )


def _experience_from_outcome(
    outcome: OutcomeRecord,
    scope: list[str],
    created_by: str | None,
) -> ExperienceRecord | None:
    if not set(outcome.owner_scope) & set(scope):
        return None
    experience_type, score = _experience_type_score(outcome.status)
    now = datetime.now(UTC)
    return ExperienceRecord(
        experience_id=f"experience-{uuid4().hex}",
        trace_id=outcome.trace_id,
        actor_id=outcome.actor_id,
        workspace_id=outcome.workspace_id,
        source_type="outcome",
        source_id=outcome.outcome_id,
        experience_type=experience_type,
        status="active",
        title=f"Outcome {outcome.status}",
        summary=outcome.summary,
        owner_scope=outcome.owner_scope,
        outcome_refs=[outcome.outcome_id],
        decision_refs=outcome.decision_refs,
        command_refs=[outcome.source_id] if outcome.source_type == "command" else [],
        workflow_refs=[outcome.source_id] if outcome.source_type == "workflow" else [],
        regression_refs=[],
        replay_refs=[],
        audit_refs=[],
        signal_refs=[],
        score=score,
        confidence=outcome.confidence,
        metadata={"dry_run": True, "outcome_status": outcome.status},
        observed_at=outcome.observed_at,
        created_by=created_by or outcome.created_by,
        created_at=now,
        updated_at=now,
    )


def _patterns_from_experiences(
    request: LearningSynthesisRequest,
    experiences: list[ExperienceRecord],
) -> list[LearningPattern]:
    grouped: dict[tuple[LearningPatternType, str, str], list[ExperienceRecord]] = {}
    for experience in experiences:
        pattern_type = pattern_type_for(experience.experience_type)
        key = (
            pattern_type,
            experience.source_type,
            normalized_summary_key(experience.summary),
        )
        grouped.setdefault(key, []).append(experience)
    patterns: list[LearningPattern] = []
    min_frequency = getattr(request, "min_frequency", 2)
    for (pattern_type, source_type, summary_key), items in sorted(grouped.items()):
        if len(items) < min_frequency:
            continue
        confidence = sum(item.confidence for item in items) / len(items)
        pattern = LearningPattern(
            pattern_id=f"learning-pattern-{uuid4().hex}",
            trace_id=request.trace_id,
            pattern_type=pattern_type,
            status="active",
            title=pattern_type.replace("_", " ").title(),
            description=f"{len(items)} {source_type} experiences matched '{summary_key}'.",
            owner_scope=request.owner_scope,
            experience_refs=[item.experience_id for item in items],
            outcome_refs=_unique(outcome_id for item in items for outcome_id in item.outcome_refs),
            evidence_refs=[],
            memory_refs=[],
            frequency=len(items),
            confidence=clamp_score(confidence),
            severity=severity_for_pattern(pattern_type, confidence),
            recommendation=recommendation_for(pattern_type),
            metadata={"dry_run": True, "summary_key": summary_key},
            created_by=request.created_by,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        patterns.append(pattern)
    return patterns


def _experience_type_score(status: str) -> tuple[ExperienceType, float]:
    if status == "verified":
        return "success", 0.9
    if status == "partial":
        return "partial_success", 0.55
    if status == "failed":
        return "failure", 0.2
    if status == "contradicted":
        return "contradiction", 0.25
    return "generic", 0.5


def _input_refs(request: LearningSynthesisRequest) -> list[str]:
    return (
        list(request.outcome_ids)
        + list(request.experience_ids)
        + list(request.pattern_ids)
        + list(request.source_types)
    )


def _dedupe_experiences(experiences: list[ExperienceRecord]) -> list[ExperienceRecord]:
    seen: set[str] = set()
    result: list[ExperienceRecord] = []
    for experience in experiences:
        if experience.experience_id in seen:
            continue
        seen.add(experience.experience_id)
        result.append(experience)
    return result


def _unique(values: Iterable[object]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value)
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def _autonomy_allows(autonomy_governor: object | None, request: LearningSynthesisRequest) -> bool:
    decide = getattr(autonomy_governor, "decide", None)
    if not callable(decide):
        return True
    try:
        decision = decide(
            action_type="learning.synthesize",
            risk_level="medium" if request.mode == "controlled" else "low",
            owner_scope=request.owner_scope,
        )
        return bool(getattr(decision, "allow", True))
    except Exception:
        return True


__all__ = ["LearningSynthesizer"]
