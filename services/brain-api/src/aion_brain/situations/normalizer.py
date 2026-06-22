"""Deterministic normalization for situation projection sources."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from aion_brain.contracts.temporal_state import (
    StateAtomCreateRequest,
    StateAtomSensitivity,
    StateAtomSourceType,
    StateAtomStatus,
    StateAtomType,
)

_SOURCE_TO_ATOM: dict[str, StateAtomType] = {
    "event": "event_state",
    "goal": "goal_state",
    "task": "task_state",
    "workflow": "workflow_state",
    "dialogue": "dialogue_state",
    "message": "dialogue_state",
    "response": "dialogue_state",
    "belief_claim": "belief_state",
    "entity": "entity_state",
    "memory": "memory_state",
    "evidence": "evidence_state",
    "approval": "approval_state",
    "policy": "policy_state",
    "autonomy": "autonomy_state",
    "operator": "operator_state",
    "kernel": "system_state",
    "system": "system_state",
}
_SOURCE_TYPES = {
    "event",
    "goal",
    "task",
    "workflow",
    "dialogue",
    "message",
    "response",
    "belief_claim",
    "entity",
    "concept",
    "memory",
    "evidence",
    "graph",
    "approval",
    "policy",
    "autonomy",
    "audit",
    "operator",
    "kernel",
    "system",
    "generic",
}
_SENSITIVITY = {"public", "internal", "confidential", "restricted"}


class SituationNormalizer:
    """Map generic source references into state atom create requests."""

    def normalize_sources(
        self,
        *,
        source_refs: list[dict[str, str]],
        owner_scope: list[str],
        trace_id: str | None,
        observed_at: datetime | None = None,
    ) -> list[StateAtomCreateRequest]:
        """Normalize refs such as {source_type, source_id, status} into atoms."""
        now = observed_at or datetime.now(UTC)
        atoms: list[StateAtomCreateRequest] = []
        for ref in source_refs:
            source_type = _source_type(ref.get("source_type") or ref.get("type"))
            source_id = ref.get("source_id") or ref.get("id")
            if not source_id:
                continue
            status = _normalize_status(ref.get("status"))
            predicate = ref.get("predicate") or "current_status"
            atom_type = _SOURCE_TO_ATOM.get(source_type, "generic")
            atoms.append(
                StateAtomCreateRequest(
                    trace_id=trace_id,
                    atom_type=atom_type,
                    source_type=source_type,
                    source_id=source_id,
                    subject_ref=ref.get("subject_ref") or source_id,
                    predicate=predicate,
                    object_ref=ref.get("object_ref"),
                    value=_value_payload(ref),
                    status=status,
                    confidence=_confidence(ref),
                    sensitivity=_sensitivity(ref.get("sensitivity")),
                    observed_at=now,
                    owner_scope=owner_scope,
                    evidence_refs=_list_ref(ref.get("evidence_ref") or ref.get("evidence_refs")),
                    belief_refs=_list_ref(ref.get("belief_ref") or ref.get("belief_refs")),
                    entity_refs=_list_ref(ref.get("entity_ref") or ref.get("entity_refs")),
                    metadata={"projection_source": True},
                )
            )
        return atoms


def _normalize_status(value: str | None) -> StateAtomStatus:
    if value in {
        "current",
        "previous",
        "stale",
        "contradicted",
        "superseded",
        "rejected",
        "unknown",
    }:
        return cast(StateAtomStatus, value)
    if value in {"active", "running", "open", "ready"}:
        return "current"
    if value in {"closed", "completed", "resolved"}:
        return "previous"
    if value in {"blocked", "failed"}:
        return "contradicted" if value == "blocked" else "stale"
    return "current"


def _source_type(value: str | None) -> StateAtomSourceType:
    if value in _SOURCE_TYPES:
        return cast(StateAtomSourceType, value)
    return "generic"


def _sensitivity(value: str | None) -> StateAtomSensitivity:
    if value in _SENSITIVITY:
        return cast(StateAtomSensitivity, value)
    return "internal"


def _confidence(ref: dict[str, str]) -> float:
    try:
        value = float(ref.get("confidence", "0.5"))
    except (TypeError, ValueError):
        return 0.5
    return max(0.0, min(1.0, value))


def _value_payload(ref: dict[str, str]) -> dict[str, Any]:
    return {
        "status": ref.get("status") or "current",
        "title": ref.get("title"),
        "summary": ref.get("summary"),
    }


def _list_ref(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    return [str(value)] if str(value) else []
