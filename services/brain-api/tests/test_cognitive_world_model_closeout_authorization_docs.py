"""AION-187 world-model closeout and workspace authorization tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

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
    ProbabilisticTransitionModel,
)

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from cognitive_architecture_governance import (  # noqa: E402
    AION185_AUTHORIZATION_ID,
    AION186_MERGE_COMMIT,
    AION186_PR,
    AION187_AUTHORIZATION_ID,
    AION187_EVALUATION_ID,
    AION188_SCOPE,
    AION188_TASK_ID,
    AION189_AUTHORIZATION_ID,
    AION189_EVALUATION_ID,
    AION191_AUTHORIZATION_ID,
    AION193_AUTHORIZATION_ID,
    AION195_AUTHORIZATION_ID,
    AION198_AUTHORIZATION_ID,
    PROGRAM_ID,
    validate_aion187_authorization_payload,
    validate_aion187_evaluation_payload,
    validate_world_model_closeout,
    validate_world_model_closeout_no_go,
)

NOW = datetime(2026, 7, 21, 12, 15, tzinfo=UTC)

REQUIRED_FILES = (
    "docs/cognitive-architecture/tasks/AION-187.md",
    "docs/cognitive-architecture/program-ledger.json",
    "docs/cognitive-architecture/authorization-ledger.json",
    "examples/cognitive-architecture/aion-187-world-model-evaluation.json",
    "examples/cognitive-architecture/aion-187-workspace-authorization.json",
    "scripts/cognitive-world-model-closeout-check.sh",
    "scripts/cognitive-world-model-closeout-no-go-regression.sh",
    "scripts/lib/cognitive_architecture_governance.py",
)


def _json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text())


def _state(state_id: str, **features: str | int | float | bool) -> WorldState:
    return WorldState(
        state_id=state_id,
        features=features,
        provenance_refs=(f"aion://aion-187/state/{state_id}",),
        observed_at=NOW,
    )


def _action(
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
        evidence_refs=(f"aion://aion-187/action/{action_id}",),
        created_at=NOW,
    )


def _transition(
    evidence_id: str,
    source: WorldState,
    action: WorldActionReference,
    outcome: WorldState,
) -> TransitionEvidence:
    return TransitionEvidence(
        evidence_id=evidence_id,
        source_state=source,
        action=action,
        outcome_state=outcome,
        evidence_refs=(f"aion://aion-187/evidence/{evidence_id}",),
        observed_at=NOW,
    )


def _synthetic_evidence() -> tuple[TransitionEvidence, ...]:
    queue = _state("state-queue", phase="queue", load=2, risk="low")
    ready = _state("state-ready", phase="ready", load=1, risk="low")
    retry = _state("state-retry", phase="retry", load=2, risk="medium")
    observe = _action("action-observe", "observe")
    stabilize = _action("action-stabilize", "stabilize")
    locked = _state("state-locked", phase="locked", load=2, risk="high")
    lock = _action("action-lock", "lock", reversible=False, irreversible_effect=True)

    evidence: list[TransitionEvidence] = []
    evidence.extend(
        _transition(f"evidence-observe-ready-{index}", queue, observe, ready)
        for index in range(9)
    )
    evidence.append(_transition("evidence-observe-retry", queue, observe, retry))
    evidence.extend(
        _transition(f"evidence-stabilize-ready-{index}", retry, stabilize, ready)
        for index in range(8)
    )
    evidence.extend(
        _transition(f"evidence-stabilize-retry-{index}", retry, stabilize, retry)
        for index in range(2)
    )
    evidence.extend(
        _transition(f"evidence-lock-locked-{index}", queue, lock, locked)
        for index in range(4)
    )
    return tuple(evidence)


def _brier_score(predictions: tuple[tuple[WorldState, WorldActionReference, str], ...]) -> float:
    model = ProbabilisticTransitionModel(evidence=_synthetic_evidence(), smoothing=0.5)
    scores: list[float] = []
    for source, action, expected_state_id in predictions:
        prediction = model.predict(source, action)
        assert prediction.fail_closed is False
        scores.append(
            sum(
                (
                    outcome.probability
                    - (1.0 if outcome.state.state_id == expected_state_id else 0.0)
                )
                ** 2
                for outcome in prediction.outcomes
            )
        )
    return sum(scores) / len(scores)


def test_aion_187_required_files_exist() -> None:
    for relative in REQUIRED_FILES:
        assert (ROOT / relative).is_file(), relative


def test_aion_187_ledgers_examples_and_no_go_validate() -> None:
    validate_world_model_closeout(ROOT)
    validate_world_model_closeout_no_go(ROOT)

    evaluation = _json("examples/cognitive-architecture/aion-187-world-model-evaluation.json")
    authorization = _json("examples/cognitive-architecture/aion-187-workspace-authorization.json")
    validate_aion187_evaluation_payload(evaluation)
    validate_aion187_authorization_payload(authorization)

    program = _json("docs/cognitive-architecture/program-ledger.json")
    auth_ledger = _json("docs/cognitive-architecture/authorization-ledger.json")

    assert program["program_id"] == PROGRAM_ID
    allowed_authorizations = {
        AION187_AUTHORIZATION_ID,
        AION189_AUTHORIZATION_ID,
        AION191_AUTHORIZATION_ID,
        AION193_AUTHORIZATION_ID,
        AION195_AUTHORIZATION_ID,
        AION198_AUTHORIZATION_ID,
    }
    active_authorization = program["active_cognitive_implementation_authorization"]
    assert active_authorization is None or active_authorization in allowed_authorizations
    assert (
        auth_ledger["active_cognitive_implementation_authorization"] is None
        or auth_ledger["active_cognitive_implementation_authorization"] in allowed_authorizations
    )
    assert auth_ledger["active_cognitive_implementation_authorization_count"] == (
        0 if active_authorization is None else 1
    )

    closed = next(
        item
        for item in auth_ledger["records"]
        if item["authorization_id"] == AION185_AUTHORIZATION_ID
    )
    active = next(
        item
        for item in auth_ledger["records"]
        if item["authorization_id"] == AION187_AUTHORIZATION_ID
    )
    assert closed["authorization_active"] is False
    assert closed["authorization_consumed"] is True
    assert closed["authorization_closeout_evaluation"] == AION187_EVALUATION_ID
    assert closed["implementation_pr"] == AION186_PR
    assert closed["implementation_merge_commit"] == AION186_MERGE_COMMIT
    assert active["implementation_task"] == AION188_TASK_ID
    assert active["scope"] == AION188_SCOPE
    if auth_ledger["active_cognitive_implementation_authorization"] == AION187_AUTHORIZATION_ID:
        assert active["authorization_active"] is True
    else:
        assert active["authorization_active"] is False
        assert active["authorization_consumed"] is True
        assert active["authorization_closeout_evaluation"] == AION189_EVALUATION_ID
        consolidation = next(
            item
            for item in auth_ledger["records"]
            if item["authorization_id"] == AION189_AUTHORIZATION_ID
        )
        if auth_ledger["active_cognitive_implementation_authorization"] == AION189_AUTHORIZATION_ID:
            assert consolidation["authorization_active"] is True
        else:
            assert consolidation["authorization_active"] is False
            assert consolidation["authorization_consumed"] is True


def test_aion_187_synthetic_world_model_evaluation_meets_thresholds() -> None:
    evidence = _synthetic_evidence()
    model = ProbabilisticTransitionModel(evidence=evidence, smoothing=0.5)
    queue = evidence[0].source_state
    observe = evidence[0].action
    retry = next(
        item.source_state for item in evidence if item.source_state.state_id == "state-retry"
    )
    stabilize = next(
        item.action for item in evidence if item.action.action_id == "action-stabilize"
    )
    unknown = _state("state-unseen", phase="unknown", load=0, risk="medium")

    holdout = (
        *((queue, observe, "state-ready") for _index in range(5)),
        *((retry, stabilize, "state-ready") for _index in range(5)),
    )
    predictions = tuple(model.predict(source, action) for source, action, _expected in holdout)
    accuracy = sum(
        prediction.outcomes[0].state.state_id == expected
        for prediction, (_source, _action, expected) in zip(predictions, holdout, strict=True)
    ) / len(predictions)
    probability_error = max(prediction.probability_sum_error for prediction in predictions)
    brier_score = _brier_score(holdout)
    unknown_predictions = tuple(model.predict(unknown, action) for action in (observe, stabilize))
    unknown_fail_closed_rate = sum(
        prediction.fail_closed and prediction.unknown_state for prediction in unknown_predictions
    ) / len(unknown_predictions)

    first_replay = tuple(prediction.fingerprint for prediction in predictions)
    second_model = ProbabilisticTransitionModel(evidence=tuple(reversed(evidence)), smoothing=0.5)
    second_replay = tuple(
        second_model.predict(source, action).fingerprint for source, action, _expected in holdout
    )
    scenario = CounterfactualScenario(
        scenario_id="scenario-aion-187-observe-stabilize",
        start_state=queue,
        actions=(observe, stabilize),
        max_depth=2,
        evidence_refs=("aion://aion-187/scenario/observe-stabilize",),
        created_at=NOW,
    )
    rollout = CounterfactualSimulator(model).simulate(scenario)
    replayed_rollout = CounterfactualSimulator(model).simulate(scenario)
    hypotheses = CausalHypothesisService().derive(evidence)

    assert accuracy >= 0.80
    assert brier_score <= 0.20
    assert round(brier_score, 3) == _json(
        "examples/cognitive-architecture/aion-187-world-model-evaluation.json"
    )["hard_pass_conditions"]["brier_score"]
    assert probability_error <= 1e-9
    assert unknown_fail_closed_rate == 1.0
    assert first_replay == second_replay
    assert rollout.replay_hash == replayed_rollout.replay_hash
    assert hypotheses
    assert all(hypothesis.evidence_refs for hypothesis in hypotheses)

    evaluation = WorldModelEvaluation(
        evaluation_id="evaluation-aion-pwme-001",
        model_version=model.model_version,
        prediction_count=len(predictions),
        transition_top_1_accuracy=accuracy,
        brier_score=brier_score,
        probability_sum_error=probability_error,
        unknown_state_fail_closed_rate=unknown_fail_closed_rate,
        deterministic_replay_rate=1.0,
        forbidden_side_effects=0,
        created_at=NOW,
    )
    assert evaluation.evaluation_name == AION187_EVALUATION_ID
    assert evaluation.runtime_effect is False


def test_aion_187_adds_no_workspace_runtime_surface() -> None:
    program = _json("docs/cognitive-architecture/program-ledger.json")
    aion188_implemented = any(
        record.get("implementation_task") == AION188_TASK_ID
        for record in program["records"]
    )
    if aion188_implemented:
        assert (ROOT / "services/brain-api/src/aion_brain/workspace").is_dir()
        assert (ROOT / "services/brain-api/src/aion_brain/contracts/workspace.py").is_file()
    else:
        assert not (ROOT / "services/brain-api/src/aion_brain/workspace").exists()
        assert not (ROOT / "services/brain-api/src/aion_brain/contracts/workspace.py").exists()
    assert not (ROOT / "services/brain-api/src/aion_brain/api/workspace.py").exists()


def test_aion_187_scripts_are_executable_and_pass() -> None:
    env = {
        **os.environ,
        "PYTEST_CURRENT_TEST": "AION-187 focused script test",
    }
    scripts = (
        "scripts/cognitive-world-model-closeout-no-go-regression.sh",
        "scripts/cognitive-world-model-closeout-check.sh",
    )
    for script in scripts:
        path = ROOT / script
        assert path.is_file()
        assert os.access(path, os.X_OK)
        subprocess.run([str(path)], cwd=ROOT, env=env, check=True)
