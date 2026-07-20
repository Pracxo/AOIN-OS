"""AION-181 disabled activation state-machine tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from test_self_improvement_shadow_activation_contracts import NOW, make_context

from aion_brain.contracts.self_improvement_shadow_activation import (
    SHADOW_ACTIVATION_ALLOWED_TRANSITIONS,
    ShadowActivationStateRecord,
)
from aion_brain.self_improvement.shadow_activation import (
    transition_shadow_activation_state,
    validate_shadow_activation_transition,
)


def test_every_legal_transition_is_accepted() -> None:
    for current, next_states in SHADOW_ACTIVATION_ALLOWED_TRANSITIONS.items():
        for next_state in next_states:
            assert validate_shadow_activation_transition(current, next_state).allowed is True


def test_illegal_active_self_and_archived_transitions_are_rejected() -> None:
    assert validate_shadow_activation_transition("drafted", "active").allowed is False
    assert validate_shadow_activation_transition("active", "drafted").allowed is False
    assert validate_shadow_activation_transition("drafted", "drafted").allowed is False
    assert validate_shadow_activation_transition("archived", "drafted").allowed is False


def test_transition_increments_sequence_without_mutating_input(tmp_path: Path) -> None:
    candidate = make_context(tmp_path)["candidate"]
    record = ShadowActivationStateRecord(
        state_record_id="state-0",
        activation_candidate_id=candidate.activation_candidate_id,
        current_state="drafted",
        sequence_number=0,
        reason_code="runtime_disabled",
        actor_principal_id="operator-requester",
        transitioned_at=NOW,
    )
    changed = transition_shadow_activation_state(
        record,
        "evidence_ready",
        actor_principal_id="operator-requester",
        reason_code="candidate_evidence_valid",
        transitioned_at=NOW,
        state_record_id="state-1",
    )
    assert record.current_state == "drafted"
    assert changed.current_state == "evidence_ready"
    assert changed.sequence_number == 1
    with pytest.raises(ValueError):
        transition_shadow_activation_state(
            changed,
            "active",
            actor_principal_id="operator-requester",
            reason_code="runtime_disabled",
            transitioned_at=NOW,
            state_record_id="state-2",
        )
