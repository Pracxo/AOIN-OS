"""Migration note service for interface drift findings."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.compatibility import InterfaceDriftFinding
from aion_brain.contracts.contract_registry import MigrationNote
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry


class MigrationNoteService:
    """Create and query informational migration notes."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        telemetry_service: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> MigrationNoteService:
        return MigrationNoteService(
            self._repository,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            actor_context=actor_context,
        )

    def create_from_finding(
        self,
        finding: InterfaceDriftFinding,
        owner_scope: list[str],
        created_by: str | None = None,
    ) -> MigrationNote:
        authorize(
            self._policy_adapter,
            action_type="contract_registry.migration_note.create",
            resource_type="migration_note",
            resource_id=finding.drift_finding_id,
            scope=owner_scope,
            trace_id=finding.trace_id,
            actor_id=created_by or self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="medium",
            context={"informational_only": True},
        )
        note = MigrationNote(
            migration_note_id=f"migration-note-{uuid4().hex}",
            trace_id=finding.trace_id,
            compatibility_scan_id=finding.compatibility_scan_id,
            finding_id=finding.drift_finding_id,
            note_type="breaking_change" if finding.breaking else "generic",
            status="open",
            title=f"Review {finding.finding_type}",
            description=finding.description,
            affected_contracts=[finding.contract_key] if finding.contract_key else [],
            affected_interfaces=[finding.interface_key] if finding.interface_key else [],
            migration_steps=[finding.recommended_action],
            owner_scope=owner_scope,
            metadata={"informational_only": True},
            created_by=created_by or self._actor_context.actor_id,
            created_at=datetime.now(UTC),
        )
        save = getattr(self._repository, "save_migration_note", None)
        stored = save(note) if callable(save) else note
        emit_telemetry(
            self._telemetry_service,
            event_type="migration_note_created",
            node_type="migration_note",
            node_id=stored.migration_note_id,
            intensity=0.6 if finding.breaking else 0.4,
            trace_id=stored.trace_id,
            payload={"finding_type": finding.finding_type, "breaking": finding.breaking},
        )
        return stored

    def list_notes(
        self,
        scope: list[str],
        status: str | None = None,
        note_type: str | None = None,
        limit: int = 100,
    ) -> list[MigrationNote]:
        authorize(
            self._policy_adapter,
            action_type="contract_registry.migration_note.read",
            resource_type="migration_note",
            resource_id=None,
            scope=scope,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        list_items = getattr(self._repository, "list_migration_notes", None)
        items = (
            list_items(status=status, note_type=note_type, limit=limit)
            if callable(list_items)
            else []
        )
        return [item for item in items if _scope_matches(item.owner_scope, scope)]

    def archive_note(
        self,
        migration_note_id: str,
        actor_id: str | None,
        reason: str,
    ) -> MigrationNote:
        get = getattr(self._repository, "get_migration_note", None)
        note = get(migration_note_id) if callable(get) else None
        if not isinstance(note, MigrationNote):
            raise ValueError("migration_note_not_found")
        authorize(
            self._policy_adapter,
            action_type="contract_registry.migration_note.update",
            resource_type="migration_note",
            resource_id=migration_note_id,
            scope=note.owner_scope,
            actor_id=actor_id or self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="medium",
            context={"reason": reason},
        )
        updated = note.model_copy(
            update={
                "status": "archived",
                "archived_at": datetime.now(UTC),
                "metadata": {**note.metadata, "archive_reason": reason},
            }
        )
        save = getattr(self._repository, "save_migration_note", None)
        stored = save(updated) if callable(save) else updated
        return stored if isinstance(stored, MigrationNote) else updated


def _scope_matches(owner_scope: list[str], scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(scope))


__all__ = ["MigrationNoteService"]
