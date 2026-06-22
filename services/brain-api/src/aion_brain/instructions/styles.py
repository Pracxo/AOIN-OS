"""Style profile manager."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.instructions import StyleProfile
from aion_brain.instructions.repository import InstructionRepository
from aion_brain.instructions.service import _authorize, _emit, _ensure_enabled, _scope_matches


class StyleProfileService:
    """Manage style profiles and compute effective style."""

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

    def create_profile(self, profile: StyleProfile) -> StyleProfile:
        _ensure_enabled(self._settings, "style_profiles_enabled", "style_profiles_disabled")
        _authorize(
            self._policy_adapter,
            "instruction.style_profile.create",
            "style_profile",
            profile.style_profile_id,
            profile.owner_scope,
            trace_id=profile.trace_id,
            actor_id=profile.actor_id,
            workspace_id=profile.workspace_id,
            risk_level="low",
        )
        stored = self._repository.save_style_profile(
            profile.model_copy(
                update={
                    "created_at": profile.created_at or datetime.now(UTC),
                    "updated_at": datetime.now(UTC),
                }
            )
        )
        _emit(
            self._telemetry_service,
            event_type="style_profile_created",
            node_type="style_profile",
            node_id=stored.style_profile_id,
            trace_id=stored.trace_id,
            intensity=0.4,
            payload={"owner_scope": stored.owner_scope, "profile_name": stored.profile_name},
        )
        return stored

    def get_profile(self, style_profile_id: str, scope: list[str]) -> StyleProfile | None:
        _authorize(
            self._policy_adapter,
            "instruction.style_profile.read",
            "style_profile",
            style_profile_id,
            scope,
        )
        profile = self._repository.get_style_profile(style_profile_id)
        if profile is None or not _scope_matches(profile.owner_scope, scope):
            return None
        return profile

    def list_profiles(
        self,
        scope: list[str],
        *,
        actor_id: str | None = None,
        workspace_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[StyleProfile]:
        _authorize(
            self._policy_adapter,
            "instruction.style_profile.read",
            "style_profile",
            None,
            scope,
        )
        return self._repository.list_style_profiles(
            scope=scope,
            actor_id=actor_id,
            workspace_id=workspace_id,
            status=status,
            limit=limit,
        )

    def disable_profile(
        self,
        style_profile_id: str,
        *,
        actor_id: str | None = None,
        reason: str | None = None,
    ) -> StyleProfile:
        profile = self._repository.get_style_profile(style_profile_id)
        if profile is None:
            raise ValueError("style_profile_not_found")
        _authorize(
            self._policy_adapter,
            "instruction.style_profile.update",
            "style_profile",
            style_profile_id,
            profile.owner_scope,
            actor_id=actor_id,
            risk_level="low",
            context={"reason": reason},
        )
        now = datetime.now(UTC)
        return self._repository.save_style_profile(
            profile.model_copy(
                update={
                    "status": "disabled",
                    "disabled_at": now,
                    "updated_at": now,
                    "metadata": {**profile.metadata, "disabled_reason": reason},
                }
            )
        )

    def effective_style(
        self,
        scope: list[str],
        *,
        actor_id: str | None = None,
        workspace_id: str | None = None,
    ) -> StyleProfile | None:
        profiles = self.list_profiles(
            scope,
            actor_id=actor_id,
            workspace_id=workspace_id,
            status="active",
            limit=100,
        )
        if profiles:
            return profiles[0]
        broader = self.list_profiles(scope, status="active", limit=100)
        return broader[0] if broader else None

    def default_style(self, scope: list[str]) -> StyleProfile:
        return StyleProfile(
            style_profile_id=f"style-profile-default-{uuid4().hex}",
            name="Default",
            description="Default AION response style profile.",
            owner_scope=scope,
            style_rules={"clarity": "clear", "structure": "structured"},
            formatting_rules={"markdown": True},
            tone_rules={"tone": "direct", "verbosity": "concise"},
            prohibited_patterns=[
                "Do not expose hidden reasoning.",
                "Do not reveal secrets.",
            ],
            status="active",
            metadata={"generated": True},
        )


__all__ = ["StyleProfileService"]
