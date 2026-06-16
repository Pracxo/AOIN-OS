"""Deterministic pattern miner for experience records."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.experience import ExperienceQuery, ExperienceRecord
from aion_brain.contracts.learning_synthesis import (
    LearningPattern,
    LearningPatternType,
    PatternMiningRequest,
    PatternMiningRun,
)
from aion_brain.learning_synthesis.patterns import (
    normalized_summary_key,
    pattern_type_for,
    recommendation_for,
    severity_for_pattern,
    source_key,
)
from aion_brain.learning_synthesis.repository import LearningSynthesisRepository
from aion_brain.outcomes._shared import audit_optional, authorize, emit_telemetry


class PatternMiner:
    """Mine generic repeated patterns without LLMs or semantic clustering."""

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

    def mine(self, request: PatternMiningRequest) -> PatternMiningRun:
        """Mine repeated generic patterns."""
        authorize(
            self._policy_adapter,
            action_type="learning.pattern.mine",
            resource_type="learning_pattern",
            resource_id=request.pattern_mining_run_id,
            scope=request.owner_scope,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            risk_level="medium" if not request.dry_run else "low",
            context={"dry_run": request.dry_run, "mining_type": request.mining_type},
        )
        run_id = request.pattern_mining_run_id or f"pattern-mining-{uuid4().hex}"
        emit_telemetry(
            self._telemetry_service,
            event_type="pattern_mining_started",
            node_type="synthesis",
            node_id=run_id,
            intensity=0.4,
            trace_id=request.trace_id,
            payload={"owner_scope": request.owner_scope, "dry_run": request.dry_run},
        )
        experiences = self._load_experiences(request)
        patterns = self._build_patterns(request, experiences)
        if not request.dry_run:
            patterns = [self._repository.save_pattern(pattern) for pattern in patterns]
        now = datetime.now(UTC)
        run = PatternMiningRun(
            pattern_mining_run_id=run_id,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            status="dry_run" if request.dry_run else "completed",
            owner_scope=request.owner_scope,
            mining_type=request.mining_type,
            input_experience_ids=[item.experience_id for item in experiences],
            patterns=patterns,
            skipped=max(0, len(experiences) - sum(pattern.frequency for pattern in patterns)),
            failed=0,
            result={
                "pattern_count": len(patterns),
                "persisted_patterns": not request.dry_run,
                "llm_used": False,
                "domain_specific": False,
            },
            created_by=request.created_by,
            created_at=now,
            completed_at=now,
        )
        stored = self._repository.save_mining_run(run)
        for pattern in patterns:
            emit_telemetry(
                self._telemetry_service,
                event_type="learning_pattern_detected",
                node_type="learning_pattern",
                node_id=pattern.pattern_id,
                intensity=pattern.confidence,
                trace_id=pattern.trace_id,
                payload={"pattern_type": pattern.pattern_type, "frequency": pattern.frequency},
            )
        audit_optional(
            self._audit_sink,
            "pattern_mining_completed",
            {"pattern_mining_run_id": stored.pattern_mining_run_id},
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="pattern_mining_completed",
            node_type="synthesis",
            node_id=stored.pattern_mining_run_id,
            intensity=0.7,
            trace_id=stored.trace_id,
            payload={"pattern_count": len(patterns), "dry_run": request.dry_run},
        )
        return stored

    def _load_experiences(self, request: PatternMiningRequest) -> list[ExperienceRecord]:
        if request.experience_ids:
            experiences = [
                item
                for experience_id in request.experience_ids
                if (item := self._repository.get_experience(experience_id)) is not None
            ]
            return experiences[: request.limit]
        query = ExperienceQuery(
            scope=request.owner_scope,
            experience_types=request.experience_types,
            include_archived=False,
            limit=request.limit,
        )
        return self._repository.query_experiences(query)

    def _build_patterns(
        self,
        request: PatternMiningRequest,
        experiences: list[ExperienceRecord],
    ) -> list[LearningPattern]:
        grouped: dict[
            tuple[LearningPatternType, str, str],
            list[ExperienceRecord],
        ] = defaultdict(list)
        for experience in experiences:
            pattern_type = pattern_type_for(experience.experience_type)
            key = (
                pattern_type,
                experience.source_type,
                normalized_summary_key(experience.summary),
            )
            grouped[key].append(experience)
        patterns: list[LearningPattern] = []
        for (pattern_type, source_type, summary_key), items in sorted(grouped.items()):
            if len(items) < request.min_frequency:
                continue
            confidence = _confidence(items)
            if confidence < request.min_confidence:
                continue
            pattern = LearningPattern(
                pattern_id=f"learning-pattern-{uuid4().hex}",
                trace_id=request.trace_id,
                pattern_type=pattern_type,
                status="active",
                title=pattern_type.replace("_", " ").title(),
                description=(
                    f"{len(items)} {source_type} experiences matched "
                    f"the generic key '{summary_key}'."
                ),
                owner_scope=request.owner_scope,
                experience_refs=[item.experience_id for item in items],
                outcome_refs=_unique(
                    outcome_id for item in items for outcome_id in item.outcome_refs
                ),
                evidence_refs=[],
                memory_refs=[],
                frequency=len(items),
                confidence=confidence,
                severity=severity_for_pattern(pattern_type, confidence),
                recommendation=recommendation_for(pattern_type),
                metadata={
                    "summary_key": summary_key,
                    "source_keys": _unique(source_key(item) for item in items),
                    "llm_used": False,
                    "semantic_clustering": False,
                },
                created_by=request.created_by,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            patterns.append(pattern)
        return patterns


def _confidence(items: list[ExperienceRecord]) -> float:
    if not items:
        return 0.0
    value = sum(item.confidence for item in items) / len(items)
    return max(0.0, min(1.0, value))


def _unique(values: Iterable[object]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value)
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


__all__ = ["PatternMiner"]
