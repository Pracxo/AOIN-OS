from __future__ import annotations

from types import SimpleNamespace

from aion_brain.action_proposals.handoffs import ExecutionHandoffService
from aion_brain.config import Settings
from aion_brain.contracts.execution_handoffs import ExecutionHandoffRequest
from tests.action_proposal_fakes import ActionFixture, AllowPolicy, proposal_request
from tests.run_supervision_fakes import RunFixture


class FakeCommandBus:
    def dispatch(self, payload: dict[str, object]) -> object:
        return SimpleNamespace(command_id=payload["command_id"])


def test_execution_handoff_creates_supervision_after_accepted_handoff() -> None:
    settings = Settings(
        _env_file=None,
        DATABASE_URL="sqlite+pysqlite:///:memory:",
        AION_ACTION_HANDOFF_CONTROLLED_ENABLED=True,
    )
    action_fixture = ActionFixture(settings=settings, policy=AllowPolicy())
    run_fixture = RunFixture()
    proposal = action_fixture.proposals.create_proposal(
        proposal_request(
            proposal_type="command",
            target_type="noop",
            target_id="target-1",
            risk_level="medium",
        )
    )
    action_fixture.repository.save_proposal(
        proposal.model_copy(update={"status": "approved_for_handoff"})
    )
    handoffs = ExecutionHandoffService(
        action_fixture.repository,
        action_fixture.policy,
        command_bus=FakeCommandBus(),
        run_supervision_service=run_fixture.supervision,
        settings=settings,
    )

    handoff = handoffs.handoff(
        ExecutionHandoffRequest(
            action_proposal_id=proposal.action_proposal_id,
            handoff_type="command_dispatch",
            target_system="command_bus",
            mode="controlled",
        )
    )
    supervised = run_fixture.repository.list_runs(scope=["workspace:main"])

    assert handoff.status == "handed_off"
    assert supervised
    assert supervised[0].source_type == "execution_handoff"
