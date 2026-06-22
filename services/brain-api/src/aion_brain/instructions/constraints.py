"""Constraint service for instruction resolution."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.instructions import ConstraintRecord
from aion_brain.instructions.repository import InstructionRepository
from aion_brain.instructions.service import _authorize, _emit, _ensure_enabled


class ConstraintService:
    """Manage generic hard and soft instruction constraints."""

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

    def create_constraint(self, constraint: ConstraintRecord) -> ConstraintRecord:
        _ensure_enabled(self._settings, "constraint_resolver_enabled", "constraints_disabled")
        _authorize(
            self._policy_adapter,
            "instruction.constraint.create",
            "instruction_constraint",
            constraint.constraint_id,
            constraint.owner_scope,
            trace_id=constraint.trace_id,
            actor_id=constraint.actor_id,
            workspace_id=constraint.workspace_id,
            risk_level="low",
            context={"constraint_type": constraint.constraint_type},
        )
        stored = self._repository.save_constraint(
            constraint.model_copy(
                update={
                    "created_at": constraint.created_at or datetime.now(UTC),
                    "updated_at": datetime.now(UTC),
                }
            )
        )
        _emit(
            self._telemetry_service,
            event_type="constraint_record_created",
            node_type="constraint",
            node_id=stored.constraint_id,
            trace_id=stored.trace_id,
            intensity=0.6,
            payload={"constraint_type": stored.constraint_type, "owner_scope": stored.owner_scope},
        )
        return stored

    def list_constraints(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        constraint_type: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[ConstraintRecord]:
        _authorize(
            self._policy_adapter,
            "instruction.constraint.read",
            "instruction_constraint",
            None,
            scope,
        )
        return self._repository.list_constraints(
            scope=scope,
            status=status,
            constraint_type=constraint_type,
            severity=severity,
            limit=limit,
        )

    def disable_constraint(
        self,
        constraint_id: str,
        *,
        actor_id: str | None = None,
        reason: str | None = None,
    ) -> ConstraintRecord:
        constraint = self._repository.get_constraint(constraint_id)
        if constraint is None:
            raise ValueError("constraint_not_found")
        if constraint.immutable:
            raise ValueError("immutable_constraint")
        _authorize(
            self._policy_adapter,
            "instruction.constraint.update",
            "instruction_constraint",
            constraint_id,
            constraint.owner_scope,
            actor_id=actor_id,
            risk_level="low",
            context={"reason": reason},
        )
        now = datetime.now(UTC)
        return self._repository.save_constraint(
            constraint.model_copy(
                update={
                    "status": "disabled",
                    "disabled_at": now,
                    "updated_at": now,
                    "metadata": {**constraint.metadata, "disabled_reason": reason},
                }
            )
        )


__all__ = ["ConstraintService"]
