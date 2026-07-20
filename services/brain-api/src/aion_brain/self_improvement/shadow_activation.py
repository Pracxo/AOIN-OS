"""Disabled shadow activation state-machine helpers."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.self_improvement_shadow_activation import (
    FORBIDDEN_SHADOW_ACTIVATION_STATES,
    SHADOW_ACTIVATION_ALLOWED_TRANSITIONS,
    SHADOW_ACTIVATION_STATES,
    ShadowActivationStateRecord,
    ShadowActivationTransitionDecision,
    ShadowActivationTransitionReason,
    require_activation_identifier,
    require_utc_datetime,
)


def validate_shadow_activation_transition(
    current_state: str,
    next_state: str,
) -> ShadowActivationTransitionDecision:
    """Validate one immutable transition in the disabled state machine."""

    if current_state in FORBIDDEN_SHADOW_ACTIVATION_STATES:
        return ShadowActivationTransitionDecision(
            current_state=current_state,
            next_state=next_state,
            allowed=False,
            reason_codes=("activation_forbidden_state_blocked",),
        )
    if next_state in FORBIDDEN_SHADOW_ACTIVATION_STATES:
        return ShadowActivationTransitionDecision(
            current_state=current_state,
            next_state=next_state,
            allowed=False,
            reason_codes=("activation_forbidden_state_blocked",),
        )
    if current_state not in SHADOW_ACTIVATION_ALLOWED_TRANSITIONS:
        return ShadowActivationTransitionDecision(
            current_state=current_state,
            next_state=next_state,
            allowed=False,
            reason_codes=("activation_transition_blocked",),
        )
    if next_state not in SHADOW_ACTIVATION_STATES:
        return ShadowActivationTransitionDecision(
            current_state=current_state,
            next_state=next_state,
            allowed=False,
            reason_codes=("activation_transition_blocked",),
        )
    if current_state == next_state:
        return ShadowActivationTransitionDecision(
            current_state=current_state,
            next_state=next_state,
            allowed=False,
            reason_codes=("activation_transition_blocked",),
        )
    allowed = next_state in SHADOW_ACTIVATION_ALLOWED_TRANSITIONS[current_state]
    return ShadowActivationTransitionDecision(
        current_state=current_state,
        next_state=next_state,
        allowed=allowed,
        reason_codes=(
            ("activation_transition_allowed",)
            if allowed
            else ("activation_transition_blocked",)
        ),
    )


def require_shadow_activation_transition(
    current_state: str,
    next_state: str,
) -> ShadowActivationTransitionDecision:
    """Require a legal disabled activation transition."""

    decision = validate_shadow_activation_transition(current_state, next_state)
    if not decision.allowed:
        raise ValueError("activation transition is not allowed")
    return decision


def transition_shadow_activation_state(
    record: ShadowActivationStateRecord,
    next_state: str,
    *,
    actor_principal_id: str,
    reason_code: ShadowActivationTransitionReason,
    transitioned_at: datetime,
    state_record_id: str,
) -> ShadowActivationStateRecord:
    """Return the next immutable state record without mutating the input."""

    require_shadow_activation_transition(record.current_state, next_state)
    return ShadowActivationStateRecord(
        state_record_id=require_activation_identifier(state_record_id, "state_record_id"),
        activation_candidate_id=record.activation_candidate_id,
        previous_state=record.current_state,
        current_state=next_state,  # type: ignore[arg-type]
        sequence_number=record.sequence_number + 1,
        reason_code=reason_code,
        actor_principal_id=require_activation_identifier(
            actor_principal_id,
            "actor_principal_id",
        ),
        transitioned_at=require_utc_datetime(transitioned_at),
    )


__all__ = [
    "SHADOW_ACTIVATION_ALLOWED_TRANSITIONS",
    "SHADOW_ACTIVATION_STATES",
    "ShadowActivationStateRecord",
    "require_shadow_activation_transition",
    "transition_shadow_activation_state",
    "validate_shadow_activation_transition",
]
