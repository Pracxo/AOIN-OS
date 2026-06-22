"""Working memory contract tests."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.working_memory import WorkingMemorySlot


def test_working_memory_slot_validates_priority_and_confidence() -> None:
    """Working memory scores stay bounded."""
    slot = working_memory_slot()
    assert slot.priority == 0.5
    with pytest.raises(ValidationError):
        working_memory_slot(priority=1.2)
    with pytest.raises(ValidationError):
        working_memory_slot(confidence=-0.1)


def test_working_memory_slot_rejects_empty_summary_and_scope() -> None:
    """Stored slots require summary and scope."""
    with pytest.raises(ValidationError):
        working_memory_slot(summary=" ")
    with pytest.raises(ValidationError):
        working_memory_slot(owner_scope=[])


def test_working_memory_slot_rejects_secret_and_chain_of_thought_keys() -> None:
    """Working memory does not store secrets or chain-of-thought."""
    with pytest.raises(ValidationError):
        working_memory_slot(content={"api_key": "hidden"})
    with pytest.raises(ValidationError):
        working_memory_slot(content={"chain_of_thought": "hidden"})


def working_memory_slot(**updates: object) -> WorkingMemorySlot:
    payload = {
        "slot_id": "slot-1",
        "focus_session_id": None,
        "trace_id": "trace-1",
        "actor_id": "actor-1",
        "workspace_id": "workspace-1",
        "slot_type": "recent_event",
        "source_type": "event",
        "source_id": "event-1",
        "content": {"event_id": "event-1"},
        "summary": "Event received",
        "priority": 0.5,
        "confidence": 0.8,
        "ttl_seconds": 3600,
        "expires_at": None,
        "pinned": False,
        "owner_scope": ["workspace:main"],
        "metadata": {},
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
        "deleted_at": None,
    }
    payload.update(updates)
    return WorkingMemorySlot.model_validate(payload)
