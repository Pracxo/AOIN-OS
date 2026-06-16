from __future__ import annotations

from aion_brain.contracts.temporal_state import StateAtom
from aion_brain.situations.transitions import StateTransitionDetector
from tests.situation_helpers import now


def _atom(atom_id: str, status: str, value: dict[str, object]) -> StateAtom:
    return StateAtom(
        state_atom_id=atom_id,
        source_type="event",
        source_id="event-1",
        predicate="status",
        value=value,
        status=status,
        confidence=0.8,
        observed_at=now(),
        owner_scope=["workspace:main"],
    )


def test_transition_detector_detects_created_and_updated() -> None:
    detector = StateTransitionDetector()

    created = detector.detect(None, _atom("atom-1", "current", {"status": "active"}))
    assert created[0].transition_type == "created"
    transitions = detector.detect(
        _atom("atom-1", "current", {"status": "active"}),
        _atom("atom-2", "stale", {"status": "stale"}),
    )

    assert {transition.transition_type for transition in transitions} == {"stale", "updated"}
