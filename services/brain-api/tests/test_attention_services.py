"""Attention and working-memory service tests."""

from datetime import UTC, datetime, timedelta

from aion_brain.attention.context_budget import ContextBudgeter
from aion_brain.attention.controller import AttentionController
from aion_brain.attention.focus import FocusService
from aion_brain.attention.interrupts import InterruptRouter
from aion_brain.attention.repository import AttentionRepository
from aion_brain.config import Settings
from aion_brain.contracts.attention import (
    AttentionDecisionRequest,
    AttentionSignalCreateRequest,
    ContextBudgetRequest,
    FocusSessionCreateRequest,
    FocusTransitionRequest,
    InterruptCreateRequest,
    InterruptDecisionRequest,
)
from aion_brain.contracts.retrieval import RetrievedContextItem
from aion_brain.contracts.working_memory import WorkingMemoryQuery, WorkingMemoryWriteRequest
from aion_brain.working_memory.repository import WorkingMemoryRepository
from aion_brain.working_memory.service import WorkingMemoryService
from tests.kernel_fakes import AllowPolicy


def test_focus_service_creates_focus_and_pauses_previous_active() -> None:
    """Only one active focus exists for actor/workspace by default."""
    focus, _wm, _controller, _interrupts, _budgeter = services()

    first = focus.create_focus_session(focus_request("first"))
    second = focus.create_focus_session(focus_request("second"))

    assert second.status == "active"
    assert focus.get_focus_session(first.focus_session_id, ["workspace:main"]).status == "paused"


def test_focus_service_transitions_active_to_paused() -> None:
    """Focus status transitions are persisted."""
    focus, _wm, _controller, _interrupts, _budgeter = services()
    session = focus.create_focus_session(focus_request("focus"))

    paused = focus.transition_focus(
        FocusTransitionRequest(
            focus_session_id=session.focus_session_id,
            to_status="paused",
            actor_id="actor-1",
            reason="pause",
        )
    )

    assert paused.status == "paused"


def test_working_memory_service_writes_queries_pins_and_deletes_slots() -> None:
    """Working memory supports create, query, pin, and soft delete."""
    _focus, wm, _controller, _interrupts, _budgeter = services()

    slot = wm.write_slot(slot_request("slot-1"))
    pinned = wm.pin_slot(slot.slot_id, ["workspace:main"])
    deleted = wm.delete_slot(slot.slot_id, ["workspace:main"])

    assert wm.query_slots(WorkingMemoryQuery(scope=["workspace:main"])) == []
    assert pinned.pinned is True
    assert deleted is True


def test_working_memory_service_excludes_expired_slots_unless_pinned() -> None:
    """Expired unpinned slots are hidden; pinned slots stay visible."""
    _focus, wm, _controller, _interrupts, _budgeter = services()
    expired = wm.write_slot(slot_request("expired", ttl_seconds=1))
    wm._repository.save(
        expired.model_copy(update={"expires_at": datetime.now(UTC) - timedelta(seconds=1)})
    )
    pinned = wm.write_slot(slot_request("pinned", pinned=True))

    results = wm.query_slots(WorkingMemoryQuery(scope=["workspace:main"]))

    assert [slot.slot_id for slot in results] == [pinned.slot_id]


def test_attention_controller_selects_top_signals_and_interrupts() -> None:
    """High-priority failure-like signals become interrupt decisions."""
    _focus, _wm, controller, _interrupts, _budgeter = services()
    signal = controller.create_signal(
        AttentionSignalCreateRequest(
            signal_type="execution_failed",
            source_type="event",
            source_id="event-1",
            title="Execution failed",
            payload={},
            urgency=0.95,
            importance=0.9,
            confidence=0.9,
            risk_level="high",
            owner_scope=["workspace:main"],
        )
    )

    decision = controller.decide(
        AttentionDecisionRequest(
            trace_id="trace-1",
            focus_session_id=None,
            actor_id="actor-1",
            workspace_id="workspace-1",
            goal="continue",
            intent_type="action.execute",
            scope=["workspace:main"],
        )
    )

    assert decision.decision_type == "interrupt"
    assert decision.selected_signal_ids == [signal.attention_signal_id]


def test_interrupt_router_creates_accepts_and_defers_interrupts() -> None:
    """Interrupt decisions update status deterministically."""
    _focus, _wm, _controller, interrupts, _budgeter = services()
    interrupt = interrupts.create_interrupt(
        InterruptCreateRequest(
            interrupt_type="generic",
            source_type="event",
            source_id="event-1",
            payload={"priority_score": 0.7, "owner_scope": ["workspace:main"]},
            owner_scope=["workspace:main"],
        )
    )
    accepted = interrupts.decide_interrupt(
        InterruptDecisionRequest(
            interrupt_id=interrupt.interrupt_id,
            decision="accept",
            actor_id="actor-1",
            reason="handle now",
        )
    )
    deferred = interrupts.decide_interrupt(
        InterruptDecisionRequest(
            interrupt_id=interrupt.interrupt_id,
            decision="defer",
            actor_id="actor-1",
            reason="later",
        )
    )

    assert accepted.status == "accepted"
    assert deferred.status == "deferred"


def test_context_budgeter_allocates_and_records_overflow() -> None:
    """ContextBudgeter allocates source quotas and records overflow."""
    _focus, _wm, _controller, _interrupts, budgeter = services()
    budget = budgeter.allocate(
        ContextBudgetRequest(
            trace_id="trace-1",
            scope=["workspace:main"],
            max_items=1,
            max_chars=20,
            requested_sources=["working_memory"],
        )
    )
    selected, overflow = budgeter.apply_budget([item("1"), item("2")], budget)

    assert len(selected) == 1
    assert overflow


def services():
    settings = Settings(_env_file=None, DATABASE_URL="sqlite+pysqlite:///:memory:")
    attention_repo = AttentionRepository("sqlite+pysqlite:///:memory:")
    policy = AllowPolicy()
    wm = WorkingMemoryService(
        WorkingMemoryRepository("sqlite+pysqlite:///:memory:"),
        policy,
        settings=settings,
    )
    focus = FocusService(attention_repo, policy)
    controller = AttentionController(
        attention_repo,
        policy,
        working_memory_service=wm,
        focus_service=focus,
        settings=settings,
    )
    interrupts = InterruptRouter(attention_repo, policy, settings=settings)
    budgeter = ContextBudgeter(attention_repo, policy)
    return focus, wm, controller, interrupts, budgeter


def focus_request(title: str) -> FocusSessionCreateRequest:
    return FocusSessionCreateRequest(
        actor_id="actor-1",
        workspace_id="workspace-1",
        owner_scope=["workspace:main"],
        title=title,
        description=f"{title} description",
    )


def slot_request(slot_id: str, **updates: object) -> WorkingMemoryWriteRequest:
    payload = {
        "slot_id": slot_id,
        "slot_type": "recent_event",
        "source_type": "event",
        "source_id": "event-1",
        "content": {"event_id": "event-1"},
        "summary": "Event received",
        "priority": 0.6,
        "confidence": 0.8,
        "owner_scope": ["workspace:main"],
    }
    payload.update(updates)
    return WorkingMemoryWriteRequest.model_validate(payload)


def item(source_id: str) -> RetrievedContextItem:
    return RetrievedContextItem(
        item_id=f"item-{source_id}",
        source="working_memory",
        source_id=source_id,
        title="slot",
        content="alpha beta",
        score=0.8,
        confidence=0.8,
        sensitivity="internal",
        owner_scope=["workspace:main"],
        memory_type="working",
        capability_id=None,
        graph_node_ids=[],
        graph_edge_ids=[],
        trace_refs=[],
        evidence_ref=None,
        metadata={},
    )
