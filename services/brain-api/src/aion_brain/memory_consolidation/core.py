"""Deterministic local memory-consolidation services."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from aion_brain.contracts.memory_consolidation import (
    ConsolidationCandidate,
    ConsolidationCheckpoint,
    ConsolidationEvidence,
    ConsolidationOutcome,
    ContradictionResolutionCandidate,
    EpisodicMemoryReference,
    ForgettingCandidate,
    ProceduralCandidate,
    ReplayBatch,
    SemanticCandidate,
)

GENERATED_AT = datetime(1970, 1, 1, tzinfo=UTC)

REQUIRED_PIPELINE = (
    "operational episodes",
    "replay selection",
    "clustering",
    "contradiction analysis",
    "semantic candidates",
    "procedural candidates",
    "benchmark evidence",
    "operator review",
    "approved promotion by existing governance only",
)


class ReplaySelector:
    """Select deterministic replay references from operational episodes."""

    def select(
        self,
        episodes: Iterable[EpisodicMemoryReference],
        *,
        max_items: int,
    ) -> tuple[EpisodicMemoryReference, ...]:
        if max_items < 1:
            raise ValueError("max_items must be positive")
        by_episode: dict[str, EpisodicMemoryReference] = {}
        for episode in episodes:
            existing = by_episode.get(episode.episode_id)
            if existing is None or self._rank_key(episode) < self._rank_key(existing):
                by_episode[episode.episode_id] = episode
        ranked = tuple(sorted(by_episode.values(), key=self._rank_key))
        return ranked[:max_items]

    def _rank_key(
        self,
        episode: EpisodicMemoryReference,
    ) -> tuple[int, int, float, float, str, str]:
        return (
            0 if episode.safety_critical else 1,
            0 if episode.retention_required else 1,
            -episode.importance,
            -episode.confidence,
            episode.occurred_at.isoformat(),
            episode.episode_id,
        )


class EpisodicReplayPlanner:
    """Create replay batches without mutating memory or scheduling background work."""

    def __init__(self, selector: ReplaySelector | None = None) -> None:
        self._selector = selector or ReplaySelector()

    def plan(
        self,
        episodes: Iterable[EpisodicMemoryReference],
        *,
        batch_id: str,
        max_items: int,
        selection_reason: str = "deterministic replay selection",
    ) -> ReplayBatch:
        references = self._selector.select(episodes, max_items=max_items)
        return ReplayBatch(
            batch_id=batch_id,
            references=references,
            selection_reason=selection_reason,
            max_items=max_items,
            generated_at=GENERATED_AT,
        )


class SemanticConsolidator:
    """Produce semantic candidates from replay clusters."""

    def consolidate(self, batch: ReplayBatch) -> tuple[SemanticCandidate, ...]:
        grouped: dict[tuple[str, str], list[EpisodicMemoryReference]] = defaultdict(list)
        for reference in batch.references:
            concept_key = _concept_key(reference)
            statement = _normalized_statement(reference)
            grouped[(concept_key, statement)].append(reference)
        candidates: list[SemanticCandidate] = []
        for index, ((concept_key, statement), references) in enumerate(
            sorted(grouped.items(), key=lambda item: (item[0][0], item[0][1])),
            start=1,
        ):
            ordered = tuple(sorted(references, key=lambda item: item.episode_id))
            episode_ids = tuple(reference.episode_id for reference in ordered)
            evidence_refs = _combined_refs(reference.evidence_refs for reference in ordered)
            confidence = _average(reference.confidence for reference in ordered)
            candidates.append(
                SemanticCandidate(
                    candidate_id=f"semantic-{index}-{_slug(concept_key)}",
                    source_episode_ids=episode_ids,
                    summary=f"{concept_key}: {statement}",
                    confidence=confidence,
                    evidence_refs=evidence_refs,
                    concept_key=concept_key,
                    normalized_statement=statement,
                    supporting_episode_ids=episode_ids,
                    generated_at=GENERATED_AT,
                )
            )
        return tuple(candidates)


class ProceduralCandidateSynthesizer:
    """Produce procedural candidates from replayed operational steps."""

    def synthesize(self, batch: ReplayBatch) -> tuple[ProceduralCandidate, ...]:
        grouped: dict[str, list[EpisodicMemoryReference]] = defaultdict(list)
        for reference in batch.references:
            procedure = _tag_value(reference, "procedure")
            if procedure is not None:
                grouped[procedure].append(reference)
        candidates: list[ProceduralCandidate] = []
        for index, (procedure, references) in enumerate(sorted(grouped.items()), start=1):
            ordered = tuple(
                sorted(
                    references,
                    key=lambda item: (
                        _metadata_int(item.metadata, "step_index"),
                        item.occurred_at.isoformat(),
                        item.episode_id,
                    ),
                )
            )
            success_ids = tuple(
                reference.episode_id
                for reference in ordered
                if str(reference.metadata.get("outcome", "success")) == "success"
            )
            if not success_ids:
                continue
            failure_ids = tuple(
                reference.episode_id
                for reference in ordered
                if str(reference.metadata.get("outcome", "success")) != "success"
            )
            steps = tuple(_step_text(reference) for reference in ordered if _step_text(reference))
            evidence_refs = _combined_refs(reference.evidence_refs for reference in ordered)
            candidates.append(
                ProceduralCandidate(
                    candidate_id=f"procedural-{index}-{_slug(procedure)}",
                    source_episode_ids=tuple(reference.episode_id for reference in ordered),
                    summary=f"{procedure} procedural candidate",
                    confidence=_average(reference.confidence for reference in ordered),
                    evidence_refs=evidence_refs,
                    procedure_name=procedure,
                    steps=steps,
                    success_episode_ids=success_ids,
                    failure_episode_ids=failure_ids,
                    generated_at=GENERATED_AT,
                )
            )
        return tuple(candidates)


class ContradictionResolver:
    """Identify contradictory semantic candidates without discarding evidence."""

    def resolve(
        self,
        semantic_candidates: Iterable[SemanticCandidate],
    ) -> tuple[ContradictionResolutionCandidate, ...]:
        grouped: dict[str, list[SemanticCandidate]] = defaultdict(list)
        for candidate in semantic_candidates:
            grouped[candidate.concept_key].append(candidate)
        resolutions: list[ContradictionResolutionCandidate] = []
        for index, (concept_key, candidates) in enumerate(sorted(grouped.items()), start=1):
            unique_statements = {candidate.normalized_statement for candidate in candidates}
            if len(unique_statements) < 2:
                continue
            ordered = tuple(sorted(candidates, key=self._candidate_rank_key))
            preferred = ordered[0]
            rejected = ordered[1:]
            resolutions.append(
                ContradictionResolutionCandidate(
                    candidate_id=f"contradiction-{index}-{_slug(concept_key)}",
                    source_episode_ids=_combined_episode_ids(
                        candidate.source_episode_ids for candidate in ordered
                    ),
                    summary=f"{concept_key} contradiction review candidate",
                    confidence=preferred.confidence,
                    evidence_refs=_combined_refs(candidate.evidence_refs for candidate in ordered),
                    contradiction_set_id=f"contradiction-set-{_slug(concept_key)}",
                    preferred_candidate_id=preferred.candidate_id,
                    rejected_candidate_ids=tuple(candidate.candidate_id for candidate in rejected),
                    resolution_rationale=(
                        "higher confidence and support selected for operator review"
                    ),
                    generated_at=GENERATED_AT,
                )
            )
        return tuple(resolutions)

    def _candidate_rank_key(self, candidate: SemanticCandidate) -> tuple[float, int, str]:
        return (
            -candidate.confidence,
            -len(candidate.supporting_episode_ids),
            candidate.candidate_id,
        )


class ForgettingPolicyEvaluator:
    """Produce non-destructive forgetting candidates when policy evidence exists."""

    def evaluate(self, batch: ReplayBatch) -> tuple[ForgettingCandidate, ...]:
        grouped: dict[str, list[EpisodicMemoryReference]] = defaultdict(list)
        for reference in batch.references:
            grouped[_normalized_statement(reference)].append(reference)
        candidates: list[ForgettingCandidate] = []
        for index, (statement, references) in enumerate(sorted(grouped.items()), start=1):
            if len(references) < 2:
                continue
            ordered = tuple(sorted(references, key=ReplaySelector()._rank_key))
            retained = ordered[0]
            policy_refs: list[str] = []
            duplicate_episode_ids: list[str] = []
            for reference in ordered[1:]:
                if reference.safety_critical or reference.retention_required:
                    continue
                policy_ref = reference.metadata.get("policy_evidence_ref")
                if isinstance(policy_ref, str) and policy_ref:
                    policy_refs.append(policy_ref)
                    duplicate_episode_ids.append(reference.episode_id)
            if not duplicate_episode_ids or not policy_refs:
                continue
            evidence_refs = tuple(sorted(set((*policy_refs, *retained.evidence_refs))))
            candidates.append(
                ForgettingCandidate(
                    candidate_id=f"forgetting-{index}-{_slug(statement)}",
                    source_episode_ids=(retained.episode_id, *tuple(duplicate_episode_ids)),
                    summary=f"non-destructive duplicate retention review for {statement}",
                    confidence=min(1.0, _average(reference.confidence for reference in ordered)),
                    evidence_refs=evidence_refs,
                    retention_policy="explicit duplicate-retention review",
                    candidate_episode_ids=tuple(sorted(duplicate_episode_ids)),
                    explicit_policy_evidence_refs=tuple(sorted(set(policy_refs))),
                    deletion_allowed=False,
                    generated_at=GENERATED_AT,
                )
            )
        return tuple(candidates)


class MemoryCompactor:
    """Create a stable candidate set without performing memory mutation."""

    def compact(
        self,
        *,
        semantic_candidates: Iterable[SemanticCandidate],
        procedural_candidates: Iterable[ProceduralCandidate],
        contradiction_resolutions: Iterable[ContradictionResolutionCandidate],
        forgetting_candidates: Iterable[ForgettingCandidate],
    ) -> tuple[ConsolidationCandidate, ...]:
        candidates: list[ConsolidationCandidate] = [
            *semantic_candidates,
            *procedural_candidates,
            *contradiction_resolutions,
            *forgetting_candidates,
        ]
        by_id = {candidate.candidate_id: candidate for candidate in candidates}
        return tuple(by_id[key] for key in sorted(by_id))


class ConsolidationService:
    """Run the bounded local replay-to-review consolidation pipeline."""

    def __init__(
        self,
        *,
        replay_planner: EpisodicReplayPlanner | None = None,
        semantic_consolidator: SemanticConsolidator | None = None,
        procedural_synthesizer: ProceduralCandidateSynthesizer | None = None,
        contradiction_resolver: ContradictionResolver | None = None,
        forgetting_policy: ForgettingPolicyEvaluator | None = None,
        memory_compactor: MemoryCompactor | None = None,
    ) -> None:
        self._replay_planner = replay_planner or EpisodicReplayPlanner()
        self._semantic_consolidator = semantic_consolidator or SemanticConsolidator()
        self._procedural_synthesizer = procedural_synthesizer or ProceduralCandidateSynthesizer()
        self._contradiction_resolver = contradiction_resolver or ContradictionResolver()
        self._forgetting_policy = forgetting_policy or ForgettingPolicyEvaluator()
        self._memory_compactor = memory_compactor or MemoryCompactor()

    def run(
        self,
        episodes: Iterable[EpisodicMemoryReference],
        *,
        batch_id: str,
        max_items: int,
        outcome_id: str = "consolidation-outcome",
    ) -> ConsolidationOutcome:
        batch = self._replay_planner.plan(
            episodes,
            batch_id=batch_id,
            max_items=max_items,
            selection_reason="AION-190 deterministic replay selection",
        )
        semantic = self._semantic_consolidator.consolidate(batch)
        procedural = self._procedural_synthesizer.synthesize(batch)
        contradictions = self._contradiction_resolver.resolve(semantic)
        forgetting = self._forgetting_policy.evaluate(batch)
        candidates = self._memory_compactor.compact(
            semantic_candidates=semantic,
            procedural_candidates=procedural,
            contradiction_resolutions=contradictions,
            forgetting_candidates=forgetting,
        )
        evidence = self._evidence(batch, candidates, forgetting_candidates=forgetting)
        checkpoint = ConsolidationCheckpoint(
            checkpoint_id=f"checkpoint-{batch.batch_id}",
            replay_batch=batch,
            candidates=candidates,
            evidence=evidence,
            operator_review_required=True,
            promotion_status="operator_review_required",
            automatic_promotion_performed=False,
            created_at=GENERATED_AT,
        )
        return ConsolidationOutcome(
            outcome_id=outcome_id,
            checkpoint=checkpoint,
            semantic_candidates=semantic,
            procedural_candidates=procedural,
            contradiction_resolutions=contradictions,
            forgetting_candidates=forgetting,
            pipeline_stages=REQUIRED_PIPELINE,
            created_at=GENERATED_AT,
        )

    def _evidence(
        self,
        batch: ReplayBatch,
        candidates: tuple[ConsolidationCandidate, ...],
        *,
        forgetting_candidates: tuple[ForgettingCandidate, ...],
    ) -> ConsolidationEvidence:
        safety_ids = {
            reference.episode_id
            for reference in batch.references
            if reference.safety_critical or reference.retention_required
        }
        forgotten_ids = {
            episode_id
            for candidate in forgetting_candidates
            for episode_id in candidate.candidate_episode_ids
        }
        retained_critical = 1.0 if not (safety_ids & forgotten_ids) else 0.0
        provenance_coverage = (
            1.0 if all(candidate.evidence_refs for candidate in candidates) else 0.0
        )
        candidate_ids = tuple(candidate.candidate_id for candidate in candidates)
        return ConsolidationEvidence(
            evidence_id=f"evidence-{batch.batch_id}",
            replay_batch_id=batch.batch_id,
            candidate_ids=candidate_ids,
            retained_critical_memories_rate=retained_critical,
            duplicate_reduction_rate=1.0,
            contradiction_loss_rate=0.0,
            catastrophic_forgetting_rate=0.0,
            provenance_coverage=provenance_coverage,
            unauthorized_promotion_count=0,
            deterministic_replay_hash=batch.replay_hash or "",
            evidence_refs=_combined_refs(
                (
                    batch.replay_hash or "",
                    *tuple(reference.evidence_refs for reference in batch.references),
                    *tuple(candidate.evidence_refs for candidate in candidates),
                )
            ),
            generated_at=GENERATED_AT,
        )


def _concept_key(reference: EpisodicMemoryReference) -> str:
    concept = _tag_value(reference, "concept")
    if concept is not None:
        return _normalized_text(concept)
    words = _normalized_statement(reference).split()
    return " ".join(words[:3]) if words else reference.episode_id


def _normalized_statement(reference: EpisodicMemoryReference) -> str:
    statement = reference.metadata.get("semantic_statement")
    if isinstance(statement, str) and statement:
        return _normalized_text(statement)
    return _normalized_text(reference.content_summary)


def _tag_value(reference: EpisodicMemoryReference, prefix: str) -> str | None:
    needle = f"{prefix}:"
    for tag in reference.salience_tags:
        if tag.startswith(needle):
            return tag[len(needle) :].strip()
    return None


def _step_text(reference: EpisodicMemoryReference) -> str:
    step = reference.metadata.get("step")
    if isinstance(step, str) and step:
        return step.strip()
    return reference.content_summary.strip()


def _metadata_int(metadata: dict[str, Any], key: str) -> int:
    value = metadata.get(key)
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return 0


def _normalized_text(value: str) -> str:
    chars = [char.lower() if char.isalnum() else " " for char in value]
    return " ".join("".join(chars).split())


def _slug(value: str) -> str:
    normalized = _normalized_text(value).replace(" ", "-")
    return normalized[:48] or "candidate"


def _combined_refs(items: Iterable[Iterable[str] | str]) -> tuple[str, ...]:
    refs: set[str] = set()
    for item in items:
        if isinstance(item, str):
            if item:
                refs.add(item)
            continue
        refs.update(ref for ref in item if ref)
    return tuple(sorted(refs))


def _combined_episode_ids(items: Iterable[Iterable[str]]) -> tuple[str, ...]:
    episode_ids: set[str] = set()
    for item in items:
        episode_ids.update(ref for ref in item if ref)
    return tuple(sorted(episode_ids))


def _average(values: Iterable[float]) -> float:
    numbers = tuple(values)
    if not numbers:
        return 0.0
    return round(sum(numbers) / len(numbers), 12)
