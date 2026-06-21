from __future__ import annotations

from aion_brain.operator.action_center import ActionCenterService
from aion_brain.operator.queues import QueueSummaryBuilder
from aion_brain.operator.repository import OperatorRepository
from tests.kernel_fakes import AllowPolicy
from tests.run_supervision_fakes import RunFixture, run_request


def test_operator_surfaces_stalled_run_and_run_queues() -> None:
    fixture = RunFixture()
    run = fixture.supervision.create(run_request())
    fixture.repository.save_run(run.model_copy(update={"status": "stalled", "stalled": True}))
    repository = OperatorRepository(database_url="sqlite+pysqlite:///:memory:")
    action_center = ActionCenterService(
        repository,
        AllowPolicy(),
        run_supervision_service=fixture.supervision,
        run_control_service=fixture.control,
        compensation_planner=fixture.compensation,
    )
    queues = QueueSummaryBuilder(
        run_supervision_service=fixture.supervision,
        run_control_service=fixture.control,
        compensation_planner=fixture.compensation,
    )

    items = action_center.build_action_items(["workspace:main"])
    summaries = queues.build_queues(["workspace:main"])

    assert any(item.recommended_action == "review_stalled_run" for item in items)
    assert any(summary.title == "Supervised Runs" for summary in summaries)
