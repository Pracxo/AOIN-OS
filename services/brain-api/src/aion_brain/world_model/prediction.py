"""Deterministic predictive world-model services."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from aion_brain.contracts.world_model import (
    CausalHypothesis,
    CounterfactualRollout,
    CounterfactualScenario,
    EffectDirection,
    ModelKind,
    OutcomePrediction,
    TransitionEvidence,
    TransitionPrediction,
    UncertaintyEstimate,
    WorldActionReference,
    WorldFeatureValue,
    WorldModelSnapshot,
    WorldState,
    fingerprint_payload,
)

GENERATED_AT = datetime(1970, 1, 1, tzinfo=UTC)


class WorldStateEncoder:
    """Encode world states into deterministic identity keys."""

    def encode(self, state: WorldState) -> str:
        """Return a stable key independent of observation timestamp."""

        return fingerprint_payload(
            {
                "state_id": state.state_id,
                "features": state.features,
                "schema_version": state.schema_version,
            }
        )


class TransitionModel(Protocol):
    """Protocol for governed transition-model adapters."""

    @property
    def model_kind(self) -> ModelKind: ...

    @property
    def model_fingerprint(self) -> str: ...

    @property
    def model_version(self) -> str: ...

    def fit(self, evidence: tuple[TransitionEvidence, ...]) -> TransitionModel: ...

    def predict(
        self,
        state: WorldState,
        action: WorldActionReference,
    ) -> TransitionPrediction: ...

    def snapshot(self) -> WorldModelSnapshot: ...


@dataclass(frozen=True)
class _EvidenceBucket:
    outcome: WorldState
    evidence: tuple[TransitionEvidence, ...]


class UncertaintyEstimator:
    """Compute bounded uncertainty from observed transition counts."""

    def estimate(
        self,
        *,
        source_state_id: str,
        action_id: str,
        probabilities: tuple[float, ...],
        sample_count: int,
        unknown_state: bool,
    ) -> UncertaintyEstimate:
        if unknown_state:
            return UncertaintyEstimate(
                uncertainty_id=f"uncertainty-{source_state_id}-{action_id}-unknown",
                source_state_id=source_state_id,
                action_id=action_id,
                sample_count=0,
                entropy=0.0,
                normalized_entropy=1.0,
                uncertainty_score=1.0,
                confidence_interval_low=0.0,
                confidence_interval_high=1.0,
                unknown_state=True,
                fail_closed=True,
            )
        entropy = -sum(
            probability * math.log(probability)
            for probability in probabilities
            if probability > 0
        )
        normalized_entropy = (
            entropy / math.log(len(probabilities))
            if len(probabilities) > 1
            else 0.0
        )
        top_probability = max(probabilities) if probabilities else 0.0
        interval_low, interval_high = _wilson_interval(top_probability, sample_count)
        uncertainty_score = min(1.0, max(0.0, normalized_entropy + (1.0 / (sample_count + 1))))
        return UncertaintyEstimate(
            uncertainty_id=f"uncertainty-{source_state_id}-{action_id}",
            source_state_id=source_state_id,
            action_id=action_id,
            sample_count=sample_count,
            entropy=entropy,
            normalized_entropy=normalized_entropy,
            uncertainty_score=uncertainty_score,
            confidence_interval_low=interval_low,
            confidence_interval_high=interval_high,
            unknown_state=False,
            fail_closed=False,
        )


class ProbabilisticTransitionModel:
    """Count-based transition model with deterministic smoothing."""

    model_kind: ModelKind = "probabilistic-counts"

    def __init__(
        self,
        *,
        evidence: tuple[TransitionEvidence, ...] = (),
        smoothing: float = 0.5,
        encoder: WorldStateEncoder | None = None,
        uncertainty_estimator: UncertaintyEstimator | None = None,
    ) -> None:
        if smoothing < 0.0:
            raise ValueError("smoothing must be non-negative")
        self._smoothing = smoothing
        self._encoder = encoder or WorldStateEncoder()
        self._uncertainty_estimator = uncertainty_estimator or UncertaintyEstimator()
        self._evidence: tuple[TransitionEvidence, ...] = ()
        self._buckets: dict[tuple[str, str], dict[str, _EvidenceBucket]] = {}
        self._state_keys: set[str] = set()
        self._action_ids: set[str] = set()
        self._fingerprint = ""
        self.fit(evidence)

    @property
    def model_fingerprint(self) -> str:
        return self._fingerprint

    @property
    def model_version(self) -> str:
        return f"{self.model_kind}/{self.model_fingerprint[:16]}"

    def fit(self, evidence: tuple[TransitionEvidence, ...]) -> TransitionModel:
        ordered_evidence = tuple(sorted(evidence, key=lambda item: item.fingerprint or ""))
        buckets: dict[tuple[str, str], dict[str, _EvidenceBucket]] = defaultdict(dict)
        state_keys: set[str] = set()
        action_ids: set[str] = set()
        for item in ordered_evidence:
            source_key = self._encoder.encode(item.source_state)
            outcome_key = self._encoder.encode(item.outcome_state)
            action_id = item.action.action_id
            key = (source_key, action_id)
            existing = buckets[key].get(outcome_key)
            evidence_tuple = (item,) if existing is None else (*existing.evidence, item)
            buckets[key][outcome_key] = _EvidenceBucket(
                outcome=existing.outcome if existing is not None else item.outcome_state,
                evidence=evidence_tuple,
            )
            state_keys.add(source_key)
            state_keys.add(outcome_key)
            action_ids.add(action_id)
        self._evidence = ordered_evidence
        self._buckets = {key: dict(value) for key, value in buckets.items()}
        self._state_keys = state_keys
        self._action_ids = action_ids
        self._fingerprint = fingerprint_payload(
            {
                "model_kind": self.model_kind,
                "smoothing": self._smoothing,
                "evidence": [item.fingerprint for item in ordered_evidence],
            }
        )
        return self

    def predict(
        self,
        state: WorldState,
        action: WorldActionReference,
    ) -> TransitionPrediction:
        state_key = self._encoder.encode(state)
        key = (state_key, action.action_id)
        buckets = self._buckets.get(key)
        if not buckets:
            uncertainty = self._uncertainty_estimator.estimate(
                source_state_id=state.state_id,
                action_id=action.action_id,
                probabilities=(),
                sample_count=0,
                unknown_state=True,
            )
            return TransitionPrediction(
                prediction_id=f"prediction-{state.state_id}-{action.action_id}-unknown",
                source_state_id=state.state_id,
                action_id=action.action_id,
                model_kind=self.model_kind,
                model_version=self.model_version,
                model_fingerprint=self.model_fingerprint,
                outcomes=(),
                uncertainty=uncertainty,
                unknown_state=True,
                fail_closed=True,
                evidence_refs=(),
                created_at=GENERATED_AT,
            )
        outcomes = self._build_outcomes(action, buckets)
        probabilities = tuple(item.probability for item in outcomes)
        total_samples = sum(item.support_count for item in outcomes)
        uncertainty = self._uncertainty_estimator.estimate(
            source_state_id=state.state_id,
            action_id=action.action_id,
            probabilities=probabilities,
            sample_count=total_samples,
            unknown_state=False,
        )
        return TransitionPrediction(
            prediction_id=f"prediction-{state.state_id}-{action.action_id}",
            source_state_id=state.state_id,
            action_id=action.action_id,
            model_kind=self.model_kind,
            model_version=self.model_version,
            model_fingerprint=self.model_fingerprint,
            outcomes=outcomes,
            uncertainty=uncertainty,
            evidence_refs=_combined_refs(bucket.evidence for bucket in buckets.values()),
            created_at=GENERATED_AT,
        )

    def snapshot(self) -> WorldModelSnapshot:
        hypotheses = CausalHypothesisService().derive(self._evidence)
        return WorldModelSnapshot(
            snapshot_id=f"world-model-snapshot-{self.model_fingerprint[:16]}",
            model_kind=self.model_kind,
            model_version=self.model_version,
            evidence_count=len(self._evidence),
            state_count=len(self._state_keys),
            action_count=len(self._action_ids),
            transition_count=sum(len(value) for value in self._buckets.values()),
            causal_hypotheses=hypotheses,
            model_fingerprint=self.model_fingerprint,
            created_at=GENERATED_AT,
        )

    def _build_outcomes(
        self,
        action: WorldActionReference,
        buckets: dict[str, _EvidenceBucket],
    ) -> tuple[OutcomePrediction, ...]:
        raw_counts = {
            outcome_key: len(bucket.evidence)
            for outcome_key, bucket in buckets.items()
        }
        denominator = sum(raw_counts.values()) + (self._smoothing * len(raw_counts))
        ranked = sorted(
            buckets.items(),
            key=lambda item: (
                -((raw_counts[item[0]] + self._smoothing) / denominator),
                item[0],
            ),
        )
        predictions: list[OutcomePrediction] = []
        for index, (outcome_key, bucket) in enumerate(ranked, start=1):
            probability = (raw_counts[outcome_key] + self._smoothing) / denominator
            confidence = min(1.0, raw_counts[outcome_key] / max(1, sum(raw_counts.values())))
            predictions.append(
                OutcomePrediction(
                    outcome_id=f"outcome-{action.action_id}-{index}",
                    state=bucket.outcome,
                    probability=probability,
                    support_count=raw_counts[outcome_key],
                    confidence=confidence,
                    reversible_effect=action.reversible,
                    irreversible_effect=action.irreversible_effect,
                    evidence_refs=_combined_refs((bucket.evidence,)),
                )
            )
        return _normalize_outcomes(tuple(predictions), action_id=action.action_id)


class DeterministicTransitionModel(ProbabilisticTransitionModel):
    """Deterministic top-outcome transition model using the same evidence index."""

    model_kind: ModelKind = "deterministic-counts"

    def __init__(
        self,
        *,
        evidence: tuple[TransitionEvidence, ...] = (),
        encoder: WorldStateEncoder | None = None,
        uncertainty_estimator: UncertaintyEstimator | None = None,
    ) -> None:
        super().__init__(
            evidence=evidence,
            smoothing=0.0,
            encoder=encoder,
            uncertainty_estimator=uncertainty_estimator,
        )

    def _build_outcomes(
        self,
        action: WorldActionReference,
        buckets: dict[str, _EvidenceBucket],
    ) -> tuple[OutcomePrediction, ...]:
        raw_counts = {
            outcome_key: len(bucket.evidence)
            for outcome_key, bucket in buckets.items()
        }
        winner_key, winner_bucket = sorted(
            buckets.items(),
            key=lambda item: (-raw_counts[item[0]], item[0]),
        )[0]
        return (
            OutcomePrediction(
                outcome_id=f"outcome-{action.action_id}-1",
                state=winner_bucket.outcome,
                probability=1.0,
                support_count=raw_counts[winner_key],
                confidence=min(1.0, raw_counts[winner_key] / max(1, sum(raw_counts.values()))),
                reversible_effect=action.reversible,
                irreversible_effect=action.irreversible_effect,
                evidence_refs=_combined_refs((winner_bucket.evidence,)),
            ),
        )


class OutcomePredictor:
    """Convenience service for next-state and action-effect comparison."""

    def __init__(self, model: TransitionModel) -> None:
        self._model = model

    def predict_next(
        self,
        state: WorldState,
        action: WorldActionReference,
    ) -> TransitionPrediction:
        return self._model.predict(state, action)

    def compare_actions(
        self,
        state: WorldState,
        actions: tuple[WorldActionReference, ...],
    ) -> tuple[TransitionPrediction, ...]:
        return tuple(
            sorted(
                (self.predict_next(state, action) for action in actions),
                key=lambda prediction: (
                    prediction.fail_closed,
                    -_top_probability(prediction),
                    prediction.action_id,
                ),
            )
        )


class CausalHypothesisService:
    """Derive explicit causal hypotheses from feature-level transitions."""

    def derive(self, evidence: tuple[TransitionEvidence, ...]) -> tuple[CausalHypothesis, ...]:
        grouped: dict[
            tuple[str, str, EffectDirection, WorldFeatureValue | None],
            list[TransitionEvidence],
        ] = defaultdict(list)
        totals_by_action_feature: Counter[tuple[str, str]] = Counter()
        for item in sorted(evidence, key=lambda value: value.fingerprint or ""):
            feature_names = sorted(
                set(item.source_state.features).union(set(item.outcome_state.features))
            )
            for feature in feature_names:
                before = item.source_state.features.get(feature)
                after = item.outcome_state.features.get(feature)
                if before == after:
                    continue
                direction = _effect_direction(before, after)
                grouped[(item.action.action_id, feature, direction, after)].append(item)
                totals_by_action_feature[(item.action.action_id, feature)] += 1
        hypotheses: list[CausalHypothesis] = []
        for index, ((action_id, feature, direction, after), items) in enumerate(
            sorted(
                grouped.items(),
                key=lambda value: (
                    value[0][0],
                    value[0][1],
                    value[0][2],
                    str(value[0][3]),
                ),
            ),
            start=1,
        ):
            total = totals_by_action_feature[(action_id, feature)]
            action = items[0].action
            support_count = len(items)
            contradicting_count = max(0, total - support_count)
            confidence = support_count / total if total else 0.0
            hypotheses.append(
                CausalHypothesis(
                    hypothesis_id=f"causal-hypothesis-{index}",
                    action_id=action_id,
                    cause_feature=f"action:{action.name}",
                    effect_feature=feature,
                    direction=direction,
                    expected_effect=after,
                    confidence=confidence,
                    support_count=support_count,
                    contradicting_count=contradicting_count,
                    reversible_effect=action.reversible,
                    irreversible_effect=action.irreversible_effect,
                    evidence_refs=_combined_refs((tuple(items),)),
                )
            )
        return tuple(hypotheses)


class CounterfactualSimulator:
    """Roll forward bounded counterfactual branches without executing actions."""

    def __init__(self, model: TransitionModel) -> None:
        self._model = model
        self._encoder = WorldStateEncoder()

    def simulate(self, scenario: CounterfactualScenario) -> CounterfactualRollout:
        frontier: dict[str, tuple[WorldState, float, int, float, bool, bool, tuple[str, ...]]] = {
            self._encoder.encode(scenario.start_state): (
                scenario.start_state,
                1.0,
                0,
                1.0,
                True,
                False,
                (),
            )
        }
        predictions: list[TransitionPrediction] = []
        for action in scenario.actions:
            next_frontier: dict[
                str,
                tuple[WorldState, float, int, float, bool, bool, tuple[str, ...]],
            ] = {}
            for (
                state,
                branch_probability,
                support,
                confidence,
                reversible,
                irreversible,
                refs,
            ) in frontier.values():
                prediction = self._model.predict(state, action)
                predictions.append(prediction)
                if prediction.fail_closed:
                    continue
                for outcome in prediction.outcomes:
                    outcome_key = self._encoder.encode(outcome.state)
                    existing = next_frontier.get(outcome_key)
                    probability = branch_probability * outcome.probability
                    merged_support = support + outcome.support_count
                    merged_confidence = min(confidence, outcome.confidence)
                    merged_reversible = reversible and outcome.reversible_effect
                    merged_irreversible = irreversible or outcome.irreversible_effect
                    merged_refs = tuple(sorted(set((*refs, *outcome.evidence_refs))))
                    if existing is not None:
                        probability += existing[1]
                        merged_support += existing[2]
                        merged_confidence = min(merged_confidence, existing[3])
                        merged_reversible = merged_reversible and existing[4]
                        merged_irreversible = merged_irreversible or existing[5]
                        merged_refs = tuple(sorted(set((*merged_refs, *existing[6]))))
                    next_frontier[outcome_key] = (
                        outcome.state,
                        probability,
                        merged_support,
                        merged_confidence,
                        merged_reversible,
                        merged_irreversible,
                        merged_refs,
                    )
            frontier = next_frontier
            if not frontier:
                break
        terminal = _normalize_terminal_distribution(frontier)
        replay_hash = fingerprint_payload(
            {
                "scenario": scenario,
                "predictions": tuple(predictions),
                "terminal_distribution": terminal,
            }
        )
        return CounterfactualRollout(
            rollout_id=f"counterfactual-rollout-{scenario.scenario_id}",
            scenario=scenario,
            predictions=tuple(predictions),
            terminal_distribution=terminal,
            replay_hash=replay_hash,
            created_at=GENERATED_AT,
        )


def _normalize_outcomes(
    outcomes: tuple[OutcomePrediction, ...],
    *,
    action_id: str,
) -> tuple[OutcomePrediction, ...]:
    total = sum(outcome.probability for outcome in outcomes)
    if total == 0.0:
        return outcomes
    normalized: list[OutcomePrediction] = []
    for index, outcome in enumerate(outcomes, start=1):
        normalized.append(
            OutcomePrediction(
                **{
                    **outcome.model_dump(mode="python", exclude={"fingerprint"}),
                    "outcome_id": f"outcome-{action_id}-{index}",
                    "probability": outcome.probability / total,
                }
            )
        )
    return tuple(normalized)


def _normalize_terminal_distribution(
    frontier: dict[str, tuple[WorldState, float, int, float, bool, bool, tuple[str, ...]]],
) -> tuple[OutcomePrediction, ...]:
    total = sum(item[1] for item in frontier.values())
    if total == 0.0:
        return ()
    outcomes: list[OutcomePrediction] = []
    ranked = sorted(frontier.values(), key=lambda item: (-item[1], item[0].fingerprint or ""))
    for index, (
        state,
        probability,
        support,
        confidence,
        reversible,
        irreversible,
        refs,
    ) in enumerate(
        ranked,
        start=1,
    ):
        outcomes.append(
            OutcomePrediction(
                outcome_id=f"terminal-{index}",
                state=state,
                probability=probability / total,
                support_count=support,
                confidence=confidence,
                reversible_effect=reversible,
                irreversible_effect=irreversible,
                evidence_refs=refs,
            )
        )
    return tuple(outcomes)


def _combined_refs(
    groups: Iterable[TransitionEvidence | Iterable[TransitionEvidence]],
) -> tuple[str, ...]:
    refs: set[str] = set()
    for group in groups:
        if isinstance(group, TransitionEvidence):
            refs.add(group.evidence_id)
            refs.update(group.evidence_refs)
        else:
            for item in group:
                refs.add(item.evidence_id)
                refs.update(item.evidence_refs)
    return tuple(sorted(refs))


def _top_probability(prediction: TransitionPrediction) -> float:
    if not prediction.outcomes:
        return 0.0
    return max(outcome.probability for outcome in prediction.outcomes)


def _effect_direction(
    before: WorldFeatureValue | None,
    after: WorldFeatureValue | None,
) -> EffectDirection:
    if before is None and after is not None:
        return "added"
    if before is not None and after is None:
        return "removed"
    if isinstance(before, int | float) and isinstance(after, int | float):
        if after > before:
            return "increased"
        if after < before:
            return "decreased"
    if before == after:
        return "unchanged"
    return "changed"


def _wilson_interval(probability: float, sample_count: int) -> tuple[float, float]:
    if sample_count <= 0:
        return 0.0, 1.0
    z = 1.96
    denominator = 1 + (z**2 / sample_count)
    centre = probability + (z**2 / (2 * sample_count))
    margin = z * math.sqrt(
        ((probability * (1 - probability)) / sample_count)
        + ((z**2) / (4 * sample_count**2))
    )
    low = max(0.0, (centre - margin) / denominator)
    high = min(1.0, (centre + margin) / denominator)
    return low, high
