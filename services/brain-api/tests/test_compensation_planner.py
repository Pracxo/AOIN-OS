from __future__ import annotations

from aion_brain.contracts.compensation import CompensationPlanCreateRequest
from tests.run_supervision_fakes import RunFixture, run_request


def test_compensation_planner_manual_review_for_unknown_run() -> None:
    fixture = RunFixture()
    run = fixture.supervision.create(
        run_request(target_system="noop", target_run_id=None, run_type="generic")
    )

    plan = fixture.compensation.propose_for_run(run.run_supervision_id, "unknown_status")

    assert plan.plan_type == "manual_review"
    assert plan.steps[0].step_type == "inspect"
    assert plan.execution_allowed is False


def test_failed_command_plan_approves_without_execution_and_converts_explicitly() -> None:
    fixture = RunFixture()
    run = fixture.supervision.create(run_request())
    fixture.repository.save_run(
        run.model_copy(update={"current_status": "failed", "status": "failed"})
    )
    plan = fixture.compensation.propose_for_run(run.run_supervision_id, "failed_command")

    assert [step.step_type for step in plan.steps[:2]] == ["inspect", "verify_outcome"]
    approved = fixture.compensation.approve_plan(
        plan.compensation_plan_id,
        actor_id="tester",
        approval_present=True,
        reason="approved",
    )
    converted = fixture.compensation.convert_steps_to_action_proposals(
        approved.compensation_plan_id,
        actor_id="tester",
        approval_present=True,
        reason="convert",
    )

    assert approved.metadata["steps_executed"] is False
    assert converted.status == "converted_to_action_proposals"
    assert fixture.action_proposals.payloads


def test_create_plan_does_not_execute_steps() -> None:
    fixture = RunFixture()
    plan = fixture.compensation.create_plan(
        CompensationPlanCreateRequest(
            source_type="generic",
            source_id="source-1",
            title="Generic plan",
            description="Generic plan",
            owner_scope=["workspace:main"],
            trigger_reason="manual",
        )
    )

    assert plan.executable is False
    assert plan.execution_allowed is False
