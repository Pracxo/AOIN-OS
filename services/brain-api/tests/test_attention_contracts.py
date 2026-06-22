"""Attention contract tests."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.attention import (
    AttentionDecision,
    AttentionSignal,
    ContextBudget,
    FocusSession,
    InterruptRecord,
)


def test_focus_session_validates_status_and_focus_type() -> None:
    """Focus sessions keep a generic lifecycle vocabulary."""
    session = focus_session()
    assert session.status == "active"
    with pytest.raises(ValidationError):
        focus_session(status="unknown")
    with pytest.raises(ValidationError):
        focus_session(focus_type="finance")


def test_focus_session_rejects_empty_owner_scope() -> None:
    """Persisted focus sessions require scope."""
    with pytest.raises(ValidationError):
        focus_session(owner_scope=[])


def test_attention_signal_validates_scores_and_domain_terms() -> None:
    """Attention signals reject bad scores and domain-specific vocabulary."""
    signal = attention_signal()
    assert signal.signal_type == "generic"
    with pytest.raises(ValidationError):
        attention_signal(urgency=1.2)
    with pytest.raises(ValidationError):
        attention_signal(title="finance alert")


def test_attention_decision_validates_priority_score_bounds() -> None:
    """Attention decisions keep priority in bounds."""
    decision = attention_decision()
    assert decision.priority_score == 0.5
    with pytest.raises(ValidationError):
        attention_decision(priority_score=-0.1)


def test_context_budget_validates_limits_and_allocation() -> None:
    """Context budgets reject invalid limits and negative allocations."""
    budget = context_budget()
    assert budget.max_items == 10
    with pytest.raises(ValidationError):
        context_budget(max_items=0)
    with pytest.raises(ValidationError):
        context_budget(allocation={"memory": -1})


def test_interrupt_record_validates_status() -> None:
    """Interrupt records keep generic statuses."""
    record = interrupt_record()
    assert record.status == "pending"
    with pytest.raises(ValidationError):
        interrupt_record(status="unknown")


def focus_session(**updates: object) -> FocusSession:
    payload = {
        "focus_session_id": "focus-1",
        "trace_id": "trace-1",
        "actor_id": "actor-1",
        "workspace_id": "workspace-1",
        "status": "active",
        "focus_type": "general",
        "active_goal_id": None,
        "active_task_id": None,
        "active_workflow_run_id": None,
        "active_trace_id": None,
        "owner_scope": ["workspace:main"],
        "title": "Focus",
        "description": "Generic focus",
        "constraints": [],
        "metadata": {},
        "started_at": datetime.now(UTC),
        "paused_at": None,
        "ended_at": None,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    payload.update(updates)
    return FocusSession.model_validate(payload)


def attention_signal(**updates: object) -> AttentionSignal:
    payload = {
        "attention_signal_id": "signal-1",
        "trace_id": "trace-1",
        "actor_id": "actor-1",
        "workspace_id": "workspace-1",
        "signal_type": "generic",
        "source_type": "event",
        "source_id": "event-1",
        "title": "Generic signal",
        "payload": {},
        "urgency": 0.5,
        "importance": 0.5,
        "confidence": 0.8,
        "risk_level": "medium",
        "owner_scope": ["workspace:main"],
        "metadata": {},
        "created_at": datetime.now(UTC),
        "handled_at": None,
    }
    payload.update(updates)
    return AttentionSignal.model_validate(payload)


def attention_decision(**updates: object) -> AttentionDecision:
    payload = {
        "attention_decision_id": "decision-1",
        "trace_id": "trace-1",
        "focus_session_id": None,
        "actor_id": None,
        "workspace_id": None,
        "decision_type": "focus",
        "selected_signal_ids": [],
        "selected_slot_ids": [],
        "selected_memory_ids": [],
        "selected_evidence_ids": [],
        "selected_skill_ids": [],
        "selected_capability_ids": [],
        "priority_score": 0.5,
        "reason": "selected",
        "constraints": [],
        "metadata": {},
        "created_at": datetime.now(UTC),
    }
    payload.update(updates)
    return AttentionDecision.model_validate(payload)


def context_budget(**updates: object) -> ContextBudget:
    payload = {
        "context_budget_id": "budget-1",
        "trace_id": "trace-1",
        "focus_session_id": None,
        "intent_id": None,
        "context_id": None,
        "max_items": 10,
        "max_chars": 1000,
        "allocation": {"working_memory": 2},
        "used_items": 0,
        "used_chars": 0,
        "overflow_items": [],
        "constraints": [],
        "created_at": datetime.now(UTC),
    }
    payload.update(updates)
    return ContextBudget.model_validate(payload)


def interrupt_record(**updates: object) -> InterruptRecord:
    payload = {
        "interrupt_id": "interrupt-1",
        "trace_id": "trace-1",
        "actor_id": "actor-1",
        "workspace_id": "workspace-1",
        "focus_session_id": None,
        "interrupt_type": "generic",
        "source_type": "event",
        "source_id": "event-1",
        "status": "pending",
        "priority_score": 0.5,
        "payload": {},
        "decision": {},
        "created_at": datetime.now(UTC),
        "resolved_at": None,
    }
    payload.update(updates)
    return InterruptRecord.model_validate(payload)
