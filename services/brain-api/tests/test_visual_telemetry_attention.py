"""Attention visual telemetry tests."""

from aion_brain.attention.context_budget import ContextBudgeter
from aion_brain.attention.controller import AttentionController
from aion_brain.attention.focus import FocusService
from aion_brain.attention.interrupts import InterruptRouter
from aion_brain.attention.repository import AttentionRepository
from aion_brain.config import Settings
from aion_brain.contracts.attention import (
    AttentionSignalCreateRequest,
    ContextBudgetRequest,
    FocusSessionCreateRequest,
    InterruptCreateRequest,
)
from aion_brain.contracts.working_memory import WorkingMemoryWriteRequest
from aion_brain.working_memory.repository import WorkingMemoryRepository
from aion_brain.working_memory.service import WorkingMemoryService
from tests.kernel_fakes import AllowPolicy


class FakeTelemetry:
    def __init__(self) -> None:
        self.events = []

    def emit(self, event):
        self.events.append(event)


def test_attention_services_emit_visual_telemetry() -> None:
    """Attention layer emits frontend-agnostic visual telemetry events."""
    telemetry = FakeTelemetry()
    settings = Settings(_env_file=None, DATABASE_URL="sqlite+pysqlite:///:memory:")
    attention_repo = AttentionRepository("sqlite+pysqlite:///:memory:")
    policy = AllowPolicy()
    focus = FocusService(attention_repo, policy, telemetry)
    working_memory = WorkingMemoryService(
        WorkingMemoryRepository("sqlite+pysqlite:///:memory:"),
        policy,
        settings=settings,
        telemetry_service=telemetry,
    )
    controller = AttentionController(
        attention_repo,
        policy,
        working_memory_service=working_memory,
        focus_service=focus,
        settings=settings,
        telemetry_service=telemetry,
    )
    interrupts = InterruptRouter(attention_repo, policy, telemetry_service=telemetry)
    budgeter = ContextBudgeter(attention_repo, policy, telemetry_service=telemetry)

    focus.create_focus_session(
        FocusSessionCreateRequest(
            owner_scope=["workspace:main"],
            title="Focus",
            description="Generic focus",
        )
    )
    working_memory.write_slot(
        WorkingMemoryWriteRequest(
            slot_type="recent_event",
            source_type="event",
            content={"event_id": "event-1"},
            summary="Event received",
            owner_scope=["workspace:main"],
        )
    )
    controller.create_signal(
        AttentionSignalCreateRequest(
            signal_type="generic",
            source_type="event",
            title="Generic signal",
            payload={},
            owner_scope=["workspace:main"],
        )
    )
    interrupt = interrupts.create_interrupt(
        InterruptCreateRequest(
            interrupt_type="generic",
            source_type="event",
            payload={"owner_scope": ["workspace:main"]},
            owner_scope=["workspace:main"],
        )
    )
    budgeter.allocate(ContextBudgetRequest(scope=["workspace:main"]))

    event_types = {event.event_type for event in telemetry.events}
    node_types = {event.node_type for event in telemetry.events}
    assert "focus_session_started" in event_types
    assert "working_memory_slot_written" in event_types
    assert "attention_signal_created" in event_types
    assert "interrupt_created" in event_types
    assert "context_budget_allocated" in event_types
    assert {"focus", "working_memory", "attention", "interrupt", "budget"} <= node_types
    assert interrupt.priority_score >= 0.5
