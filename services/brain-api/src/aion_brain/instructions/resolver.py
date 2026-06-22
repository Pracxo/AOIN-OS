"""Deterministic instruction hierarchy resolver."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.instructions import (
    ConstraintRecord,
    InstructionConflict,
    InstructionRecord,
    InstructionResolutionRequest,
    InstructionResolutionResult,
    InstructionSourceType,
)
from aion_brain.contracts.preferences import PreferenceRecord
from aion_brain.instructions.normalizer import (
    detect_forbidden_override_attempt,
    normalize_instruction_text,
)
from aion_brain.instructions.repository import InstructionRepository
from aion_brain.instructions.service import _authorize, _emit

PRECEDENCE_ORDER = [
    "policy/hard safety",
    "runtime config",
    "autonomy",
    "risk/approval",
    "capability/sandbox",
    "current-session instructions",
    "task/workflow instructions",
    "workspace instructions",
    "confirmed actor preferences",
    "learned preference candidates",
]
_HARD_CONSTRAINT_TYPES = {
    "policy",
    "runtime",
    "autonomy",
    "risk",
    "approval",
    "capability",
    "sandbox",
}
_INLINE_PRECEDENCE = {
    "current_session": 6,
    "task": 7,
    "workflow": 7,
    "workspace": 8,
}


class InstructionResolver:
    """Resolve effective instructions without weakening hard AION boundaries."""

    def __init__(
        self,
        repository: InstructionRepository,
        policy_adapter: object | None,
        *,
        conflict_detector: object | None = None,
        style_service: object | None = None,
        telemetry_service: object | None = None,
        settings: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._conflict_detector = conflict_detector
        self._style_service = style_service
        self._telemetry_service = telemetry_service
        self._settings = settings

    def resolve(self, request: InstructionResolutionRequest) -> InstructionResolutionResult:
        """Resolve active instructions, confirmed preferences, constraints, and style."""

        if self._settings is not None and not bool(
            getattr(self._settings, "constraint_resolver_enabled", True)
        ):
            raise RuntimeError("constraint_resolver_disabled")
        _authorize(
            self._policy_adapter,
            "instruction.resolve",
            "instruction_resolution",
            request.trace_id,
            request.owner_scope,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            risk_level="low",
            context={"precedence_order": PRECEDENCE_ORDER},
        )
        constraints = self._active_constraints(request) if request.include_constraints else []
        persisted_instructions = self._active_instructions(request)
        inline_instructions = _inline_instructions(request)
        all_instructions = [*inline_instructions, *persisted_instructions]
        preferences = self._preferences(request) if request.include_preferences else []
        effective_constraints = sorted(
            constraints,
            key=lambda item: (_constraint_rank(item), item.created_at or datetime.min),
        )
        effective_instructions, suppressed = _effective_instructions(all_instructions)
        effective_preferences, preference_suppressed = _effective_preferences(
            preferences,
            include_candidates=request.include_candidate_preferences,
        )
        suppressed.extend(preference_suppressed)
        conflicts = self._detect_conflicts(
            effective_instructions,
            effective_preferences,
            effective_constraints,
            request,
        )
        hard_keys = {constraint.constraint_key for constraint in effective_constraints}
        safe_preferences: list[PreferenceRecord] = []
        for preference in effective_preferences:
            if preference.preference_key in hard_keys:
                suppressed.append(
                    {
                        "type": "preference",
                        "id": preference.preference_id,
                        "reason": "suppressed_by_hard_constraint",
                    }
                )
                continue
            safe_preferences.append(preference)
        style_profile = (
            _effective_style(
                self._style_service,
                request.owner_scope,
                request.actor_id,
                request.workspace_id,
            )
            if request.include_style
            else None
        )
        effective_style = (
            style_profile.model_dump(mode="json") if hasattr(style_profile, "model_dump") else {}
        )
        resolution_run_id = request.resolution_run_id or f"instruction-resolution-{uuid4().hex}"
        now = datetime.now(UTC)
        applied_instruction_ids = [item.instruction_id for item in effective_instructions]
        applied_preference_ids = [item.preference_id for item in safe_preferences]
        applied_constraint_ids = [item.constraint_id for item in effective_constraints]
        suppressed_instruction_ids = [
            str(item.get("id"))
            for item in suppressed
            if item.get("type") == "instruction" and item.get("id")
        ]
        resolution = InstructionResolutionResult(
            resolution_run_id=resolution_run_id,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            status="warning" if conflicts else "completed",
            owner_scope=request.owner_scope,
            applied_instruction_ids=applied_instruction_ids,
            applied_preference_ids=applied_preference_ids,
            applied_constraint_ids=applied_constraint_ids,
            suppressed_instruction_ids=suppressed_instruction_ids,
            effective_style=effective_style,
            effective_instructions=[item.instruction_text for item in effective_instructions],
            conflicts=conflicts,
            suppressed=suppressed,
            precedence_order=PRECEDENCE_ORDER,
            constraints=[
                "hard_boundaries_precede_preferences",
                "hidden_reasoning_disallowed",
                "policy_autonomy_approval_runtime_capability_sandbox_limits_preserved",
            ],
            result={
                "preference_count": len(safe_preferences),
                "constraint_count": len(effective_constraints),
                "suppressed_count": len(suppressed),
            },
            created_by=request.created_by,
            created_at=now,
            completed_at=now,
        )
        if bool(getattr(self._settings, "instruction_resolution_store_runs", True)):
            self._repository.save_resolution_run(
                resolution_run_id=resolution.resolution_id,
                trace_id=request.trace_id,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                owner_scope=request.owner_scope,
                request=request.model_dump(mode="json"),
                result=resolution.model_dump(mode="json"),
                status="completed",
            )
        _emit(
            self._telemetry_service,
            event_type="instruction_resolution_completed",
            node_type="instruction_resolution",
            node_id=resolution.resolution_id,
            trace_id=resolution.trace_id,
            intensity=0.6,
            payload={
                "instruction_count": len(effective_instructions),
                "preference_count": len(safe_preferences),
                "conflict_count": len(conflicts),
            },
        )
        return resolution

    def _active_constraints(self, request: InstructionResolutionRequest) -> list[ConstraintRecord]:
        return self._repository.list_constraints(
            scope=request.owner_scope,
            status="active",
            limit=1000,
        )

    def _active_instructions(
        self,
        request: InstructionResolutionRequest,
    ) -> list[InstructionRecord]:
        records = self._repository.list_instructions(
            scope=request.owner_scope,
            status=None if request.include_disabled else "active",
            limit=1000,
        )
        if request.instruction_ids:
            requested = set(request.instruction_ids)
            records = [record for record in records if record.instruction_id in requested]
        now = datetime.now(UTC)
        return [
            record
            for record in records
            if request.include_disabled
            or (
                record.status == "active"
                and (record.effective_from is None or record.effective_from <= now)
                and (record.expires_at is None or record.expires_at > now)
            )
        ]

    def _preferences(self, request: InstructionResolutionRequest) -> list[PreferenceRecord]:
        records = self._repository.list_preferences(
            scope=request.owner_scope,
            status=None,
            limit=1000,
        )
        if request.preference_ids:
            requested = set(request.preference_ids)
            records = [record for record in records if record.preference_id in requested]
        return records

    def _detect_conflicts(
        self,
        instructions: list[InstructionRecord],
        preferences: list[PreferenceRecord],
        constraints: list[ConstraintRecord],
        request: InstructionResolutionRequest,
    ) -> list[InstructionConflict]:
        detect = getattr(self._conflict_detector, "detect_conflicts", None)
        if not callable(detect):
            return []
        conflicts = detect(
            instructions=instructions,
            preferences=preferences,
            constraints=constraints,
            owner_scope=request.owner_scope,
            trace_id=request.trace_id,
        )
        create_conflict = getattr(self._conflict_detector, "create_conflict", None)
        if callable(create_conflict):
            stored = []
            for conflict in conflicts:
                try:
                    stored.append(create_conflict(conflict))
                except Exception:
                    stored.append(conflict)
            return stored
        return list(conflicts)


def _inline_instructions(request: InstructionResolutionRequest) -> list[InstructionRecord]:
    records: list[InstructionRecord] = []
    for source, texts in (
        ("current_session", request.current_session_instructions),
        ("task", request.task_instructions),
        ("workflow", request.workflow_instructions),
        ("workspace", request.workspace_instructions),
    ):
        for index, text in enumerate(texts):
            records.append(
                InstructionRecord(
                    instruction_id=f"instruction-inline-{source}-{index}-{uuid4().hex}",
                    trace_id=request.trace_id,
                    actor_id=request.actor_id,
                    workspace_id=request.workspace_id,
                    instruction_type="session_instruction"
                    if source == "current_session"
                    else "generic",
                    scope_type="dialogue_session" if source == "current_session" else "workspace",
                    owner_scope=request.owner_scope,
                    source_type=cast(InstructionSourceType, source),
                    instruction_text=text,
                    normalized_instruction=normalize_instruction_text(text),
                    priority=800 if source == "current_session" else 500,
                    precedence_rank=_INLINE_PRECEDENCE[source],
                    status="active",
                    metadata={"inline": True},
                    created_by=request.actor_id,
                    created_at=datetime.now(UTC),
                )
            )
    return records


def _effective_instructions(
    records: list[InstructionRecord],
) -> tuple[list[InstructionRecord], list[dict[str, Any]]]:
    suppressed: list[dict[str, Any]] = []
    safe_records: list[InstructionRecord] = []
    seen_content: set[str] = set()
    for record in sorted(
        records,
        key=lambda item: (
            item.precedence_rank or _instruction_rank(item),
            -item.priority,
            item.created_at or datetime.min,
        ),
    ):
        if detect_forbidden_override_attempt(record.instruction_text):
            suppressed.append(
                {
                    "type": "instruction",
                    "id": record.instruction_id,
                    "reason": "forbidden_override_attempt",
                }
            )
            continue
        normalized = record.normalized_instruction or normalize_instruction_text(
            record.instruction_text
        )
        if normalized in seen_content:
            suppressed.append(
                {"type": "instruction", "id": record.instruction_id, "reason": "duplicate"}
            )
            continue
        seen_content.add(normalized)
        safe_records.append(record.model_copy(update={"normalized_instruction": normalized}))
    return safe_records, suppressed


def _effective_preferences(
    records: list[PreferenceRecord],
    *,
    include_candidates: bool,
) -> tuple[list[PreferenceRecord], list[dict[str, Any]]]:
    effective: list[PreferenceRecord] = []
    suppressed: list[dict[str, Any]] = []
    by_key: dict[str, PreferenceRecord] = {}
    for record in sorted(
        records,
        key=lambda item: (item.confidence, item.created_at or datetime.min),
        reverse=True,
    ):
        if record.status != "confirmed" and not include_candidates:
            suppressed.append(
                {
                    "type": "preference",
                    "id": record.preference_id,
                    "reason": "unconfirmed_preference",
                }
            )
            continue
        if record.status in {"rejected", "disabled"}:
            suppressed.append(
                {"type": "preference", "id": record.preference_id, "reason": record.status}
            )
            continue
        if record.preference_key in by_key:
            suppressed.append(
                {"type": "preference", "id": record.preference_id, "reason": "lower_confidence"}
            )
            continue
        by_key[record.preference_key] = record
        effective.append(record)
    return effective, suppressed


def _constraint_rank(record: ConstraintRecord) -> int:
    constraint_type = (
        "runtime" if record.constraint_type == "runtime_config" else record.constraint_type
    )
    if constraint_type in _HARD_CONSTRAINT_TYPES:
        return 0
    return 1


def _instruction_rank(record: InstructionRecord) -> int:
    if record.instruction_type in {"policy", "safety"} or record.source_type == "policy":
        return 1
    if record.instruction_type == "runtime" or record.source_type == "runtime_config":
        return 2
    if record.instruction_type == "capability":
        return 5
    if record.instruction_type == "session_instruction":
        return 6
    if record.instruction_type in {"task_instruction", "workflow"}:
        return 7
    if record.instruction_type == "workspace_instruction":
        return 8
    if record.instruction_type in {"actor_preference", "learned_candidate"}:
        return 9
    return 8


def _effective_style(
    style_service: object | None,
    scope: list[str],
    actor_id: str | None,
    workspace_id: str | None,
) -> object | None:
    effective_style = getattr(style_service, "effective_style", None)
    if not callable(effective_style):
        return None
    try:
        return cast(
            object | None,
            effective_style(scope, actor_id=actor_id, workspace_id=workspace_id),
        )
    except Exception:
        return None


__all__ = ["InstructionResolver", "PRECEDENCE_ORDER"]
