from __future__ import annotations

from aion_brain.run_supervision.targets import RunTargetStatusAdapter
from tests.run_supervision_fakes import FakeCommandBus, FakeWorkflowService


def test_target_status_adapter_maps_command_status() -> None:
    adapter = RunTargetStatusAdapter(command_bus=FakeCommandBus(status="running"))

    sample = adapter.sample(
        "command_bus",
        "command-1",
        {"run_supervision_id": "run-1", "scope": ["workspace:main"]},
    )

    assert sample.observed_status == "running"


def test_target_status_adapter_maps_workflow_status() -> None:
    adapter = RunTargetStatusAdapter(workflow_service=FakeWorkflowService(status="failed"))

    sample = adapter.sample(
        "workflow_engine",
        "workflow-run-1",
        {"run_supervision_id": "run-1", "scope": ["workspace:main"]},
    )

    assert sample.observed_status == "failed"
