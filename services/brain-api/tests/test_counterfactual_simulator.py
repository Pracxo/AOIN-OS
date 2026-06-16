from __future__ import annotations

from aion_brain.contracts.counterfactuals import CounterfactualRunRequest
from aion_brain.contracts.decisions import DecisionFrameCreateRequest, DecisionOptionCreateRequest
from tests.decision_helpers import bundle


def test_counterfactual_dry_run_mutates_no_source_records_and_projects_effects() -> None:
    services = bundle()
    frame = services.frame_service.create_frame(
        DecisionFrameCreateRequest(
            title="Choose",
            question="Which option?",
            owner_scope=["workspace:main"],
        )
    )
    option = services.option_service.create_option(
        DecisionOptionCreateRequest(
            decision_frame_id=frame.decision_frame_id,
            title="Option",
            description="Generic option.",
            expected_effects=[{"effect_type": "state_note", "value": "changed"}],
        )
    )

    run = services.counterfactuals.run(
        CounterfactualRunRequest(
            decision_frame_id=frame.decision_frame_id,
            decision_option_id=option.decision_option_id,
            owner_scope=["workspace:main"],
        )
    )

    assert run.status == "dry_run"
    assert run.projected_changes == [{"effect_type": "state_note", "value": "changed"}]
    assert run.result["mutated_source_records"] is False
    assert "missing_evidence" in run.unknowns
