"""Deterministic state transition detection."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from aion_brain.contracts.temporal_state import StateAtom, StateTransition, StateTransitionType


class StateTransitionDetector:
    """Detect generic changes between previous and current state atoms."""

    def detect(self, previous: StateAtom | None, current: StateAtom) -> list[StateTransition]:
        if previous is None:
            return [_transition("created", None, current, "State atom was created.")]
        transitions: list[StateTransition] = []
        if previous.status != current.status:
            transitions.append(
                _transition(
                    _transition_type_for_status(current.status),
                    previous,
                    current,
                    "State atom status changed.",
                )
            )
        if previous.value != current.value:
            transitions.append(
                _transition("updated", previous, current, "State atom value changed.")
            )
        return transitions


def _transition(
    transition_type: StateTransitionType,
    previous: StateAtom | None,
    current: StateAtom,
    reason: str,
) -> StateTransition:
    return StateTransition(
        state_transition_id=f"state-transition-{uuid4().hex}",
        trace_id=current.trace_id,
        situation_id=current.situation_id,
        transition_type=transition_type,
        from_state_atom_id=previous.state_atom_id if previous else None,
        to_state_atom_id=current.state_atom_id,
        source_type=current.source_type,
        source_id=current.source_id,
        status="detected",
        confidence=min(current.confidence, previous.confidence if previous else current.confidence),
        reason=reason,
        evidence_refs=current.evidence_refs,
        metadata={"deterministic": True},
        created_at=datetime.now(UTC),
    )


def _transition_type_for_status(status: str) -> StateTransitionType:
    if status in {"superseded", "contradicted", "stale"}:
        return cast(StateTransitionType, status)
    if status == "previous":
        return "completed"
    if status == "rejected":
        return "failed"
    return "updated"
