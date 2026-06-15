"""Workflow autonomy integration tests."""

from aion_brain.contracts.workflows import WorkflowRunRequest
from tests.autonomy_fakes import FakeAutonomyGovernor
from tests.test_local_workflow_engine import FakePolicyAdapter, make_create_request, make_engine


def test_workflow_engine_blocks_run_when_autonomy_denies() -> None:
    """Local workflows persist a blocked run when autonomy denies execution."""
    engine = make_engine()
    workflow = engine.create_workflow(make_create_request(activate=True))
    engine._autonomy_governor = FakeAutonomyGovernor(allow=False)  # noqa: SLF001

    run = engine.run_workflow(WorkflowRunRequest(workflow_id=workflow.workflow_id))

    assert run.status == "blocked_by_policy"
    assert run.error["reason"] == "autonomy_denied"


def test_workflow_engine_still_calls_policy_when_autonomy_allows() -> None:
    """Autonomy approval keeps the normal policy boundary active."""
    policy = FakePolicyAdapter()
    engine = make_engine(policy_adapter=policy)
    workflow = engine.create_workflow(make_create_request(activate=True))
    engine._autonomy_governor = FakeAutonomyGovernor()  # noqa: SLF001

    run = engine.run_workflow(WorkflowRunRequest(workflow_id=workflow.workflow_id))

    assert run.status == "completed"
    assert "workflow.run" in [request.action_type for request in policy.requests]
