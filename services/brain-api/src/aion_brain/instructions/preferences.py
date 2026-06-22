"""Preference ledger service."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.preferences import PreferenceRecord
from aion_brain.instructions.repository import InstructionRepository
from aion_brain.instructions.service import _authorize, _emit, _ensure_enabled, _scope_matches


class PreferenceService:
    """Manage confirmed and candidate preferences without auto-confirming."""

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

    def create_preference(self, preference: PreferenceRecord) -> PreferenceRecord:
        """Create one preference. Learned/default preferences stay candidates."""

        _ensure_enabled(self._settings, "preferences_enabled", "preferences_disabled")
        _authorize(
            self._policy_adapter,
            "preference.create",
            "preference",
            preference.preference_id,
            preference.owner_scope,
            trace_id=preference.trace_id,
            actor_id=preference.actor_id,
            workspace_id=preference.workspace_id,
            risk_level="low",
            context={"preference_type": preference.preference_type},
        )
        status = preference.status
        if (
            status == "confirmed"
            and preference.metadata.get("learned") is True
            and not bool(getattr(self._settings, "preference_auto_confirm_enabled", False))
        ):
            status = "candidate"
        stored = self._repository.save_preference(
            preference.model_copy(
                update={
                    "status": status,
                    "created_at": preference.created_at or datetime.now(UTC),
                    "updated_at": datetime.now(UTC),
                }
            )
        )
        _emit(
            self._telemetry_service,
            event_type="preference_created",
            node_type="preference",
            node_id=stored.preference_id,
            trace_id=stored.trace_id,
            intensity=0.5,
            payload={"owner_scope": stored.owner_scope, "preference_key": stored.preference_key},
        )
        return stored

    def get_preference(self, preference_id: str, scope: list[str]) -> PreferenceRecord | None:
        """Return one preference visible to scope."""

        _authorize(self._policy_adapter, "preference.read", "preference", preference_id, scope)
        record = self._repository.get_preference(preference_id)
        if record is None or not _scope_matches(record.owner_scope, scope):
            return None
        return record

    def list_preferences(
        self,
        scope: list[str],
        *,
        actor_id: str | None = None,
        workspace_id: str | None = None,
        status: str | None = None,
        preference_type: str | None = None,
        limit: int = 100,
    ) -> list[PreferenceRecord]:
        """List preferences visible to scope."""

        _authorize(self._policy_adapter, "preference.read", "preference", None, scope)
        return self._repository.list_preferences(
            scope=scope,
            actor_id=actor_id,
            workspace_id=workspace_id,
            status=status,
            preference_type=preference_type,
            limit=limit,
        )

    def confirm_preference(
        self,
        preference_id: str,
        *,
        actor_id: str | None = None,
        reason: str | None = None,
    ) -> PreferenceRecord:
        return self._set_status(preference_id, "confirmed", actor_id=actor_id, reason=reason)

    def reject_preference(
        self,
        preference_id: str,
        *,
        actor_id: str | None = None,
        reason: str | None = None,
    ) -> PreferenceRecord:
        return self._set_status(preference_id, "rejected", actor_id=actor_id, reason=reason)

    def disable_preference(
        self,
        preference_id: str,
        *,
        actor_id: str | None = None,
        reason: str | None = None,
    ) -> PreferenceRecord:
        return self._set_status(preference_id, "disabled", actor_id=actor_id, reason=reason)

    def _set_status(
        self,
        preference_id: str,
        status: str,
        *,
        actor_id: str | None,
        reason: str | None,
    ) -> PreferenceRecord:
        record = self._repository.get_preference(preference_id)
        if record is None:
            raise ValueError("preference_not_found")
        _authorize(
            self._policy_adapter,
            "preference.update",
            "preference",
            preference_id,
            record.owner_scope,
            actor_id=actor_id,
            risk_level="low",
            context={"status": status, "reason": reason},
        )
        now = datetime.now(UTC)
        updates: dict[str, object] = {
            "status": status,
            "updated_at": now,
            "metadata": {**record.metadata, "resolution_reason": reason},
        }
        if status == "confirmed":
            updates["confirmed_at"] = now
        elif status == "rejected":
            updates["rejected_at"] = now
        elif status == "disabled":
            updates["disabled_at"] = now
        stored = self._repository.save_preference(record.model_copy(update=updates))
        event_type = {
            "confirmed": "preference_confirmed",
            "rejected": "preference_rejected",
            "disabled": "preference_rejected",
        }[status]
        _emit(
            self._telemetry_service,
            event_type=event_type,
            node_type="preference",
            node_id=stored.preference_id,
            trace_id=stored.trace_id,
            intensity=0.6,
            payload={"status": status, "owner_scope": stored.owner_scope},
        )
        return stored


__all__ = ["PreferenceService"]
