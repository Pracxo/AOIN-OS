"""Planner to action proposal integration tests."""

from __future__ import annotations

from aion_brain.contracts.context import ContextPacket
from aion_brain.planning.planner import Planner


class ProposalSpy:
    def __init__(self) -> None:
        self.requests: list[object] = []

    def create_proposal(self, request: object) -> None:
        self.requests.append(request)


def _context(create_action_proposals: bool) -> ContextPacket:
    return ContextPacket(
        context_id="context-1",
        intent_id="intent-1",
        goal="generic goal",
        known_context=[{"intent_type": "goal.plan"}],
        retrieved_memory_ids=[],
        available_capability_ids=[],
        constraints=[],
        open_questions=[],
        execution_limits={
            "create_action_proposals": create_action_proposals,
            "owner_scope": ["workspace:main"],
            "trace_id": "trace-1",
        },
    )


def test_planner_creates_proposals_only_when_execution_limit_requests_it() -> None:
    proposal_spy = ProposalSpy()
    planner = Planner(action_proposal_service=proposal_spy)

    planner.create_plan(_context(False))
    assert proposal_spy.requests == []

    plan = planner.create_plan(_context(True))

    assert len(proposal_spy.requests) == len(plan.steps)
