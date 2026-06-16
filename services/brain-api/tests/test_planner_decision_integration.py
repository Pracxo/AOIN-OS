from __future__ import annotations

from aion_brain.contracts.context import ContextPacket
from aion_brain.planning.planner import Planner


class FakeFrameService:
    def __init__(self) -> None:
        self.created = False

    def create_frame(self, request: object) -> object:
        self.created = True
        return type("Frame", (), {"decision_frame_id": "frame-1"})()


def test_planner_creates_decision_frame_only_when_requested() -> None:
    service = FakeFrameService()
    planner = Planner(decision_frame_service=service)
    context = ContextPacket(
        context_id="context-1",
        intent_id="intent-1",
        goal="choose",
        known_context=[{"intent_type": "goal.plan"}],
        retrieved_memory_ids=[],
        available_capability_ids=[],
        constraints=[],
        open_questions=[],
        execution_limits={},
    )

    plan = planner.create_plan(context)

    assert "decision_frame_id" not in plan.metadata
    assert service.created is False

    plan_with_frame = planner.create_plan(
        context.model_copy(update={"execution_limits": {"create_decision_frame": True}})
    )

    assert plan_with_frame.metadata["decision_frame_id"] == "frame-1"


def test_dialogue_decision_integration_is_opt_in_by_metadata() -> None:
    assert (
        "create_decision_frame"
        not in ContextPacket(
            context_id="context-1",
            intent_id="intent-1",
            goal="choose",
            known_context=[],
            retrieved_memory_ids=[],
            available_capability_ids=[],
            constraints=[],
            open_questions=[],
            execution_limits={},
        ).execution_limits
    )
