from __future__ import annotations

from aion_brain.contracts.counterfactuals import CounterfactualRunRequest
from aion_brain.contracts.decisions import DecisionFrameCreateRequest, DecisionOptionCreateRequest
from aion_brain.decisions.counterfactuals import CounterfactualSimulator
from aion_brain.decisions.frames import DecisionFrameService
from aion_brain.decisions.options import DecisionOptionService
from aion_brain.decisions.repository import DecisionRepository
from tests.outcome_helpers import AllowPolicy, bundle


def test_decision_expected_effects_created_only_when_metadata_requests_them() -> None:
    outcomes = bundle()
    decisions = DecisionRepository()
    policy = AllowPolicy()
    frames = DecisionFrameService(decisions, policy)
    options = DecisionOptionService(
        decisions,
        policy,
        expected_effect_service=outcomes.expected,
    )
    frame = frames.create_frame(
        DecisionFrameCreateRequest(
            title="Choose",
            question="Which?",
            owner_scope=["workspace:main"],
        )
    )
    options.create_option(
        DecisionOptionCreateRequest(
            decision_frame_id=frame.decision_frame_id,
            title="Plain",
            description="No effects.",
            expected_effects=[{"predicate": "status"}],
        )
    )
    assert outcomes.repository.list_expected_effects(source_type="decision_option") == []

    stored = options.create_option(
        DecisionOptionCreateRequest(
            decision_frame_id=frame.decision_frame_id,
            title="With effects",
            description="Creates expected effects.",
            expected_effects=[{"predicate": "status", "effect_type": "status_change"}],
            metadata={"create_expected_effects": True},
        )
    )

    effects = outcomes.repository.list_expected_effects(
        source_type="decision_option",
        source_id=stored.decision_option_id,
    )
    assert len(effects) == 1


def test_counterfactual_expected_effects_created_only_when_metadata_requests_them() -> None:
    outcomes = bundle()
    decisions = DecisionRepository()
    policy = AllowPolicy()
    frames = DecisionFrameService(decisions, policy)
    options = DecisionOptionService(decisions, policy)
    simulator = CounterfactualSimulator(
        decisions,
        policy,
        expected_effect_service=outcomes.expected,
    )
    frame = frames.create_frame(
        DecisionFrameCreateRequest(
            title="Choose",
            question="Which?",
            owner_scope=["workspace:main"],
        )
    )
    option = options.create_option(
        DecisionOptionCreateRequest(
            decision_frame_id=frame.decision_frame_id,
            title="Option",
            description="Projects.",
            expected_effects=[{"predicate": "status", "effect_type": "status_change"}],
        )
    )

    simulator.run(
        CounterfactualRunRequest(
            decision_frame_id=frame.decision_frame_id,
            decision_option_id=option.decision_option_id,
            owner_scope=["workspace:main"],
        )
    )
    assert outcomes.repository.list_expected_effects(source_type="counterfactual") == []

    run = simulator.run(
        CounterfactualRunRequest(
            decision_frame_id=frame.decision_frame_id,
            decision_option_id=option.decision_option_id,
            owner_scope=["workspace:main"],
            metadata={"create_expected_effects": True},
        )
    )
    effects = outcomes.repository.list_expected_effects(
        source_type="counterfactual",
        source_id=run.counterfactual_run_id,
    )
    assert len(effects) == 1
