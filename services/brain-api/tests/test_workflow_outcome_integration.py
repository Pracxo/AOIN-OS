from __future__ import annotations

from aion_brain.contracts.workflows import WorkflowCreateRequest, WorkflowRunRequest, WorkflowStep
from tests.kernel_fakes import kernel_container


def test_workflow_completion_creates_outcome_when_enabled() -> None:
    container = kernel_container()
    workflow = container.local_workflow_engine.create_workflow(
        WorkflowCreateRequest(
            name="Generic workflow",
            description="Test workflow.",
            owner_scope=["workspace:main"],
            steps=[
                WorkflowStep(
                    step_id="step-1",
                    action_type="noop",
                    description="Noop step.",
                    input_template={},
                    expected_output={},
                    risk_level="low",
                    timeout_seconds=None,
                    retryable=False,
                    metadata={},
                )
            ],
            activate=True,
        )
    )

    run = container.local_workflow_engine.run_workflow(
        WorkflowRunRequest(workflow_id=workflow.workflow_id, mode="dry_run")
    )

    outcomes = container.outcome_repository.list_outcomes(scope=["workspace:main"])
    assert run.status == "completed"
    assert any(item.source_id == run.workflow_run_id for item in outcomes)
