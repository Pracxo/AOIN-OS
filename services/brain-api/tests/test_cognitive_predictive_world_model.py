"""AION-186 predictive world-model service tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.world_model import (
    CounterfactualScenario,
    TransitionEvidence,
    WorldActionReference,
    WorldModelEvaluation,
    WorldState,
)
from aion_brain.world_model import (
    CausalHypothesisService,
    CounterfactualSimulator,
    DeterministicTransitionModel,
    InMemoryWorldModelRepository,
    OutcomePredictor,
    ProbabilisticTransitionModel,
    WorldStateEncoder,
)
from aion_brain.world_model.repository import DuplicateTransitionEvidenceError

NOW = datetime(2026, 7, 21, 10, 0, tzinfo=UTC)


def state(state_id: str, **features: str | int | float | bool) -> WorldState:
    return WorldState(
        state_id=state_id,
        features=features,
        provenance_refs=(f"aion://world-state/{state_id}",),
        observed_at=NOW,
    )


def action(
    action_id: str,
    name: str,
    *,
    reversible: bool = True,
    irreversible_effect: bool = False,
) -> WorldActionReference:
    return WorldActionReference(
        action_id=action_id,
        name=name,
        reversible=reversible,
        irreversible_effect=irreversible_effect,
        evidence_refs=(f"aion://world-action/{action_id}",),
        created_at=NOW,
    )


def transition(
    evidence_id: str,
    source: WorldState,
    world_action: WorldActionReference,
    outcome: WorldState,
) -> TransitionEvidence:
    return TransitionEvidence(
        evidence_id=evidence_id,
        source_state=source,
        action=world_action,
        outcome_state=outcome,
        evidence_refs=(f"aion://transition/{evidence_id}",),
        observed_at=NOW,
    )


def synthetic_evidence() -> tuple[TransitionEvidence, ...]:
    idle = state("state-idle", location="hub", status="idle", load=1)
    ready = state("state-ready", location="hub", status="ready", load=2)
    retry = state("state-retry", location="hub", status="retry", load=1)
    locked = state("state-locked", location="vault", status="locked", load=2)
    inspect = action("action-inspect", "inspect")
    lock = action("action-lock", "lock", reversible=False, irreversible_effect=True)
    return (
        transition("evidence-inspect-1", idle, inspect, ready),
        transition("evidence-inspect-2", idle, inspect, ready),
        transition("evidence-inspect-3", idle, inspect, ready),
        transition("evidence-inspect-4", idle, inspect, retry),
        transition("evidence-lock-1", idle, lock, locked),
        transition("evidence-lock-2", idle, lock, locked),
    )


def test_contracts_are_immutable_redacted_and_fingerprinted() -> None:
    world_state = state("state-contract", status="ready", load=2)
    same_state = WorldState(
        state_id="state-contract",
        features={"load": 2, "status": "ready"},
        provenance_refs=("aion://world-state/state-contract",),
        observed_at=NOW,
    )

    assert world_state.fingerprint == same_state.fingerprint
    assert world_state.features["status"] == "ready"

    with pytest.raises(ValidationError):
        world_state.state_id = "changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        world_state.features["status"] = "changed"
    with pytest.raises(ValidationError):
        WorldState(state_id="unsafe", features={"api_key": "sk-test"}, observed_at=NOW)


def test_append_only_repository_rejects_conflicting_duplicate_evidence() -> None:
    evidence = synthetic_evidence()[0]
    repository = InMemoryWorldModelRepository()

    first = repository.append_evidence(evidence)
    duplicate = repository.append_evidence(evidence)

    assert first.duplicate is False
    assert duplicate.duplicate is True
    assert repository.latest_sequence() == 1
    with pytest.raises(DuplicateTransitionEvidenceError):
        repository.append_evidence(
            transition(
                "evidence-inspect-1",
                state("state-other", location="edge", status="idle"),
                action("action-inspect", "inspect"),
                state("state-outcome", location="edge", status="ready"),
            )
        )


def test_probabilistic_prediction_supports_multiple_futures_and_normalizes() -> None:
    evidence = synthetic_evidence()
    idle = evidence[0].source_state
    inspect = evidence[0].action
    model = ProbabilisticTransitionModel(evidence=evidence, smoothing=0.5)

    prediction = model.predict(idle, inspect)

    assert prediction.unknown_state is False
    assert prediction.fail_closed is False
    assert len(prediction.outcomes) == 2
    assert prediction.outcomes[0].state.state_id == "state-ready"
    assert prediction.outcomes[0].probability == pytest.approx(0.7)
    assert prediction.outcomes[1].probability == pytest.approx(0.3)
    assert prediction.probability_sum_error <= 1e-9
    assert prediction.uncertainty.sample_count == 4
    assert 0.0 <= prediction.uncertainty.uncertainty_score <= 1.0
    assert prediction.model_fingerprint == model.model_fingerprint
    assert prediction.model_version == model.model_version


def test_unknown_state_predictions_fail_closed_without_outcomes() -> None:
    model = ProbabilisticTransitionModel(evidence=synthetic_evidence())
    unknown = state("state-unseen", location="edge", status="unknown")
    inspect = action("action-inspect", "inspect")

    prediction = model.predict(unknown, inspect)

    assert prediction.unknown_state is True
    assert prediction.fail_closed is True
    assert prediction.outcomes == ()
    assert prediction.uncertainty.unknown_state is True
    assert prediction.uncertainty.fail_closed is True
    assert prediction.uncertainty.uncertainty_score == 1.0


def test_action_effect_comparison_and_irreversible_flags() -> None:
    evidence = synthetic_evidence()
    idle = evidence[0].source_state
    inspect = evidence[0].action
    lock = evidence[-1].action
    predictor = OutcomePredictor(ProbabilisticTransitionModel(evidence=evidence))

    predictions = predictor.compare_actions(idle, (inspect, lock))
    lock_prediction = next(item for item in predictions if item.action_id == "action-lock")

    assert predictions[0].action_id == "action-lock"
    assert lock_prediction.outcomes[0].irreversible_effect is True
    assert lock_prediction.outcomes[0].reversible_effect is False
    assert lock_prediction.outcomes[0].probability == 1.0


def test_causal_hypotheses_include_provenance() -> None:
    hypotheses = CausalHypothesisService().derive(synthetic_evidence())
    status_ready = next(
        item
        for item in hypotheses
        if item.action_id == "action-inspect"
        and item.effect_feature == "status"
        and item.expected_effect == "ready"
    )

    assert status_ready.support_count == 3
    assert status_ready.contradicting_count == 1
    assert status_ready.confidence == pytest.approx(0.75)
    assert "evidence-inspect-1" in status_ready.evidence_refs


def test_counterfactual_rollouts_are_branching_and_deterministic() -> None:
    evidence = synthetic_evidence()
    idle = evidence[0].source_state
    inspect = evidence[0].action
    model = ProbabilisticTransitionModel(evidence=evidence)
    scenario = CounterfactualScenario(
        scenario_id="scenario-inspect",
        start_state=idle,
        actions=(inspect,),
        max_depth=2,
        evidence_refs=("aion://scenario/inspect",),
        created_at=NOW,
    )

    first = CounterfactualSimulator(model).simulate(scenario)
    second = CounterfactualSimulator(model).simulate(scenario)

    assert len(first.predictions) == 1
    assert len(first.terminal_distribution) == 2
    assert first.terminal_distribution[0].state.state_id == "state-ready"
    assert first.replay_hash == second.replay_hash
    assert first.fingerprint == second.fingerprint


def test_deterministic_model_replay_uses_stable_tie_breaking() -> None:
    evidence = synthetic_evidence()
    idle = evidence[0].source_state
    inspect = evidence[0].action
    first = DeterministicTransitionModel(evidence=evidence).predict(idle, inspect)
    second = DeterministicTransitionModel(evidence=tuple(reversed(evidence))).predict(idle, inspect)

    assert first.outcomes[0].state.state_id == "state-ready"
    assert first.outcomes[0].probability == 1.0
    assert first.fingerprint == second.fingerprint


def test_snapshot_and_evaluation_contracts_preserve_no_side_effects() -> None:
    model = ProbabilisticTransitionModel(evidence=synthetic_evidence())
    snapshot = model.snapshot()
    encoder = WorldStateEncoder()

    assert snapshot.runtime_effect is False
    assert snapshot.model_weights_changed is False
    assert snapshot.evidence_count == 6
    assert snapshot.causal_hypotheses
    assert encoder.encode(synthetic_evidence()[0].source_state)

    evaluation = WorldModelEvaluation(
        evaluation_id="evaluation-aion-pwme-001-smoke",
        model_version=model.model_version,
        prediction_count=6,
        transition_top_1_accuracy=0.83,
        brier_score=0.17,
        probability_sum_error=0.0,
        unknown_state_fail_closed_rate=1.0,
        deterministic_replay_rate=1.0,
        forbidden_side_effects=0,
        created_at=NOW,
    )
    assert evaluation.evaluated_task == "AION-186"
    with pytest.raises(ValidationError):
        WorldModelEvaluation(
            evaluation_id="evaluation-side-effect",
            model_version=model.model_version,
            prediction_count=1,
            transition_top_1_accuracy=1.0,
            brier_score=0.0,
            probability_sum_error=0.0,
            unknown_state_fail_closed_rate=1.0,
            deterministic_replay_rate=1.0,
            forbidden_side_effects=1,
            created_at=NOW,
        )
