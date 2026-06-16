"""Utility profile service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.decisions import (
    UtilityProfile,
    UtilityProfileCreateRequest,
    generic_balanced_weights,
)
from aion_brain.decisions._shared import authorize, emit_telemetry, scope_matches
from aion_brain.decisions.repository import DecisionRepository


class UtilityProfileService:
    """Manage generic deterministic utility profiles."""

    def __init__(
        self,
        repository: DecisionRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def create_profile(self, request: UtilityProfileCreateRequest) -> UtilityProfile:
        authorize(
            self._policy_adapter,
            action_type="decision.utility_profile.create",
            resource_type="utility_profile",
            resource_id=request.utility_profile_id,
            scope=request.owner_scope,
            risk_level="low",
            context={"name": request.name},
        )
        now = datetime.now(UTC)
        profile = UtilityProfile(
            utility_profile_id=request.utility_profile_id or f"utility-profile-{uuid4().hex}",
            name=request.name,
            description=request.description,
            status="active",
            owner_scope=request.owner_scope,
            weights=request.weights,
            constraints=request.constraints,
            metadata=request.metadata,
            created_by=request.created_by,
            created_at=now,
            updated_at=now,
        )
        stored = self._repository.save_profile(profile)
        emit_telemetry(
            self._telemetry_service,
            event_type="utility_profile_created",
            node_type="utility_profile",
            node_id=stored.utility_profile_id,
            intensity=0.4,
            trace_id=None,
            payload={"owner_scope": stored.owner_scope, "name": stored.name},
        )
        return stored

    def get_profile(self, name_or_id: str, scope: list[str]) -> UtilityProfile | None:
        authorize(
            self._policy_adapter,
            action_type="decision.utility_profile.read",
            resource_type="utility_profile",
            resource_id=name_or_id,
            scope=scope,
        )
        profile = self._repository.get_profile(name_or_id)
        if profile is None or not scope_matches(profile.owner_scope, scope):
            return None
        return profile

    def list_profiles(self, scope: list[str], status: str | None = None) -> list[UtilityProfile]:
        authorize(
            self._policy_adapter,
            action_type="decision.utility_profile.read",
            resource_type="utility_profile",
            resource_id=None,
            scope=scope,
        )
        return self._repository.list_profiles(scope=scope, status=status)

    def disable_profile(
        self,
        utility_profile_id: str,
        actor_id: str | None,
        reason: str,
        scope: list[str],
    ) -> UtilityProfile:
        profile = self.get_profile(utility_profile_id, scope)
        if profile is None:
            raise ValueError("utility_profile_not_found")
        authorize(
            self._policy_adapter,
            action_type="decision.utility_profile.update",
            resource_type="utility_profile",
            resource_id=utility_profile_id,
            scope=scope,
            actor_id=actor_id,
            context={"reason": reason},
        )
        disabled = profile.model_copy(
            update={
                "status": "disabled",
                "disabled_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "metadata": {**profile.metadata, "disable_reason": reason},
            }
        )
        return self._repository.save_profile(disabled)

    def seed_default_profiles(
        self,
        *,
        dry_run: bool = True,
        owner_scope: list[str],
    ) -> dict[str, object]:
        request = UtilityProfileCreateRequest(
            name="generic-balanced",
            description="Balanced generic utility profile for deterministic v0.1 decisions.",
            owner_scope=owner_scope,
            weights=generic_balanced_weights(),
            metadata={"seed": "aion-v0.1"},
        )
        if dry_run:
            return {"dry_run": True, "profiles": [request.model_dump(mode="json")]}
        existing = self._repository.get_profile("generic-balanced")
        if existing is not None:
            return {"dry_run": False, "profiles": [existing.model_dump(mode="json")]}
        return {
            "dry_run": False,
            "profiles": [self.create_profile(request).model_dump(mode="json")],
        }

    def default_profile(self, owner_scope: list[str]) -> UtilityProfile:
        existing = self._repository.get_profile("generic-balanced")
        if existing is not None:
            return existing
        return self.create_profile(
            UtilityProfileCreateRequest(
                name="generic-balanced",
                description="Balanced generic utility profile for deterministic v0.1 decisions.",
                owner_scope=owner_scope,
                weights=generic_balanced_weights(),
                metadata={"seed": "auto"},
            )
        )
