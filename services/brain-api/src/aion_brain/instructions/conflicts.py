"""Instruction conflict detection."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from aion_brain.contracts.instructions import (
    ConstraintRecord,
    InstructionConflict,
    InstructionConflictType,
    InstructionRecord,
    InstructionSeverity,
)
from aion_brain.contracts.preferences import PreferenceRecord
from aion_brain.instructions.normalizer import detect_forbidden_override_attempt
from aion_brain.instructions.repository import InstructionRepository
from aion_brain.instructions.service import _authorize, _emit


class InstructionConflictDetector:
    """Detect and persist generic instruction conflicts."""

    def __init__(
        self,
        repository: InstructionRepository,
        policy_adapter: object | None,
        *,
        telemetry_service: object | None = None,
        settings: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._settings = settings

    def detect_conflicts(
        self,
        *,
        instructions: list[InstructionRecord],
        preferences: list[PreferenceRecord],
        constraints: list[ConstraintRecord],
        owner_scope: list[str],
        trace_id: str | None = None,
    ) -> list[InstructionConflict]:
        if self._settings is not None and not bool(
            getattr(self._settings, "instruction_conflict_detection_enabled", True)
        ):
            return []
        conflicts: list[InstructionConflict] = []
        for instruction in instructions:
            if detect_forbidden_override_attempt(instruction.content):
                conflicts.append(
                    _conflict(
                        "policy_override_attempt",
                        "critical",
                        owner_scope,
                        trace_id or instruction.trace_id,
                        "Instruction attempts to override a hard AION boundary.",
                        instruction_ids=[instruction.instruction_id],
                    )
                )
            if _grounding_conflict_text(instruction.content):
                conflicts.append(
                    _conflict(
                        "grounding_conflict",
                        "high",
                        owner_scope,
                        trace_id or instruction.trace_id,
                        "Instruction weakens grounding requirements.",
                        instruction_ids=[instruction.instruction_id],
                    )
                )
        conflicts.extend(_style_conflicts(preferences, owner_scope, trace_id))
        hard_constraint_keys = {
            constraint.constraint_key
            for constraint in constraints
            if constraint.constraint_type
            in {"policy", "runtime", "autonomy", "risk", "approval", "capability", "sandbox"}
        }
        for preference in preferences:
            if preference.preference_key in hard_constraint_keys:
                conflicts.append(
                    _conflict(
                        "policy_override_attempt",
                        "high",
                        owner_scope,
                        trace_id or preference.trace_id,
                        "Preference conflicts with a hard constraint key.",
                        preference_ids=[preference.preference_id],
                    )
                )
        return _dedupe_conflicts(conflicts)

    def create_conflict(self, conflict: InstructionConflict) -> InstructionConflict:
        _authorize(
            self._policy_adapter,
            "instruction.conflict.update",
            "instruction_conflict",
            conflict.conflict_id,
            conflict.owner_scope,
            trace_id=conflict.trace_id,
            actor_id=conflict.actor_id,
            workspace_id=conflict.workspace_id,
            risk_level="low",
        )
        stored = self._repository.save_conflict(
            conflict.model_copy(update={"created_at": conflict.created_at or datetime.now(UTC)})
        )
        _emit(
            self._telemetry_service,
            event_type="instruction_conflict_detected",
            node_type="instruction_conflict",
            node_id=stored.conflict_id,
            trace_id=stored.trace_id,
            intensity=1.0 if stored.severity in {"high", "critical"} else 0.7,
            payload={"conflict_type": stored.conflict_type, "severity": stored.severity},
        )
        return stored

    def list_conflicts(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[InstructionConflict]:
        _authorize(
            self._policy_adapter,
            "instruction.conflict.read",
            "instruction_conflict",
            None,
            scope,
        )
        return self._repository.list_conflicts(
            scope=scope,
            status=status,
            severity=severity,
            limit=limit,
        )

    def resolve_conflict(
        self,
        conflict_id: str,
        *,
        resolution: str,
        actor_id: str | None = None,
        reason: str | None = None,
    ) -> InstructionConflict:
        conflict = self._repository.get_conflict(conflict_id)
        if conflict is None:
            raise ValueError("instruction_conflict_not_found")
        _authorize(
            self._policy_adapter,
            "instruction.conflict.update",
            "instruction_conflict",
            conflict_id,
            conflict.owner_scope,
            actor_id=actor_id,
            risk_level="low",
            context={"reason": reason},
        )
        stored = self._repository.save_conflict(
            conflict.model_copy(
                update={
                    "status": "resolved",
                    "resolution": resolution,
                    "resolved_at": datetime.now(UTC),
                    "metadata": {**conflict.metadata, "resolution_reason": reason},
                }
            )
        )
        _emit(
            self._telemetry_service,
            event_type="instruction_conflict_resolved",
            node_type="instruction_conflict",
            node_id=stored.conflict_id,
            trace_id=stored.trace_id,
            intensity=0.5,
            payload={"resolution": resolution},
        )
        return stored


def _conflict(
    conflict_type: str,
    severity: str,
    owner_scope: list[str],
    trace_id: str | None,
    description: str,
    *,
    instruction_ids: list[str] | None = None,
    preference_ids: list[str] | None = None,
) -> InstructionConflict:
    return InstructionConflict(
        conflict_id=f"instruction-conflict-{uuid4().hex}",
        trace_id=trace_id,
        conflict_type=cast(InstructionConflictType, conflict_type),
        severity=cast(InstructionSeverity, severity),
        status="open",
        owner_scope=owner_scope,
        instruction_ids=instruction_ids or [],
        preference_ids=preference_ids or [],
        reason=description,
        metadata={"detected": True},
    )


def _style_conflicts(
    preferences: list[PreferenceRecord],
    owner_scope: list[str],
    trace_id: str | None,
) -> list[InstructionConflict]:
    by_key: dict[str, PreferenceRecord] = {}
    conflicts: list[InstructionConflict] = []
    for preference in preferences:
        if (
            preference.preference_type not in {"style", "response_style", "formatting", "verbosity"}
            or preference.status != "confirmed"
        ):
            continue
        previous = by_key.get(preference.preference_key)
        if previous is None:
            by_key[preference.preference_key] = preference
            continue
        if previous.preference_value != preference.preference_value:
            conflicts.append(
                _conflict(
                    "style_conflict",
                    "medium",
                    owner_scope,
                    trace_id or preference.trace_id,
                    "Confirmed style preferences disagree for the same key.",
                    preference_ids=[previous.preference_id, preference.preference_id],
                )
            )
    return conflicts


def _grounding_conflict_text(value: str) -> bool:
    lowered = value.lower()
    return "without evidence" in lowered or "ungrounded" in lowered


def _dedupe_conflicts(conflicts: list[InstructionConflict]) -> list[InstructionConflict]:
    seen: set[tuple[str, str, tuple[str, ...], tuple[str, ...]]] = set()
    unique: list[InstructionConflict] = []
    for conflict in conflicts:
        key = (
            conflict.conflict_type,
            conflict.description,
            tuple(conflict.instruction_ids),
            tuple(conflict.preference_ids),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(conflict)
    return unique


__all__ = ["InstructionConflictDetector"]
