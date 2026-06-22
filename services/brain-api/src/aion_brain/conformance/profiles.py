"""Conformance profile service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import AIONNotFoundException
from aion_brain.config import Settings, get_settings
from aion_brain.conformance.policy import authorize_conformance_action
from aion_brain.conformance.redaction import redact_conformance_payload
from aion_brain.conformance.repository import ConformanceRepository
from aion_brain.conformance.telemetry import emit_conformance_telemetry
from aion_brain.contracts.conformance import (
    ConformanceProfile,
    ConformanceProfileCreateRequest,
)


class ConformanceProfileService:
    """Manage metadata-only conformance profiles."""

    def __init__(
        self,
        repository: ConformanceRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._settings = settings or get_settings()

    def create_profile(self, request: ConformanceProfileCreateRequest) -> ConformanceProfile:
        if not self._settings.conformance_profiles_enabled:
            raise RuntimeError("conformance_profiles_disabled")
        authorize_conformance_action(
            self._policy_adapter,
            "conformance.profile.create",
            request.owner_scope,
            actor_id=request.created_by,
            resource_type="conformance_profile",
            risk_level="medium",
        )
        now = datetime.now(UTC)
        profile = ConformanceProfile(
            conformance_profile_id=(
                request.conformance_profile_id or f"conformance-profile-{uuid4().hex}"
            ),
            name=request.name,
            description=request.description,
            status="active",
            profile_type=request.profile_type,
            owner_scope=request.owner_scope,
            required_checks=request.required_checks,
            optional_checks=request.optional_checks,
            minimum_score=request.minimum_score,
            fail_on_critical=request.fail_on_critical,
            fail_on_missing_contract=request.fail_on_missing_contract,
            fail_on_missing_policy_action=request.fail_on_missing_policy_action,
            fail_on_missing_sandbox=request.fail_on_missing_sandbox,
            metadata=redact_conformance_payload(
                {**request.metadata, "metadata_only": True, "activation_allowed": False}
            ),
            created_by=request.created_by,
            created_at=now,
            updated_at=now,
        )
        saved = self._repository.save_profile(profile)
        emit_conformance_telemetry(
            self._telemetry_service,
            event_type="conformance_profile_created",
            node_type="conformance_profile",
            node_id=saved.conformance_profile_id,
            scope=saved.owner_scope,
            intensity=0.4,
            payload={"profile_type": saved.profile_type},
        )
        return saved

    def get_profile(
        self,
        conformance_profile_id: str,
        scope: list[str],
    ) -> ConformanceProfile | None:
        authorize_conformance_action(
            self._policy_adapter,
            "conformance.profile.read",
            scope,
            resource_type="conformance_profile",
            resource_id=conformance_profile_id,
        )
        return self._repository.get_profile(conformance_profile_id)

    def require_profile(self, conformance_profile_id: str, scope: list[str]) -> ConformanceProfile:
        profile = self.get_profile(conformance_profile_id, scope)
        if profile is None:
            raise AIONNotFoundException("conformance_profile_not_found")
        return profile

    def list_profiles(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        profile_type: str | None = None,
        limit: int = 100,
    ) -> list[ConformanceProfile]:
        authorize_conformance_action(
            self._policy_adapter,
            "conformance.profile.read",
            scope,
            resource_type="conformance_profile",
        )
        return self._repository.list_profiles(
            status=status,
            profile_type=profile_type,
            limit=limit,
        )

    def disable_profile(
        self,
        conformance_profile_id: str,
        scope: list[str],
        actor_id: str | None,
        reason: str,
    ) -> ConformanceProfile:
        authorize_conformance_action(
            self._policy_adapter,
            "conformance.profile.update",
            scope,
            actor_id=actor_id,
            resource_type="conformance_profile",
            resource_id=conformance_profile_id,
            risk_level="medium",
        )
        profile = self.require_profile(conformance_profile_id, scope)
        return self._repository.save_profile(
            profile.model_copy(
                update={
                    "status": "disabled",
                    "disabled_at": datetime.now(UTC),
                    "metadata": {**profile.metadata, "disabled_reason": reason},
                }
            )
        )

    def seed_default_profiles(self, scope: list[str], dry_run: bool = True) -> dict[str, Any]:
        defaults = _default_profiles(scope)
        if dry_run:
            return {
                "dry_run": True,
                "created": [],
                "profiles": [item.model_dump(mode="json") for item in defaults],
            }
        created = [self.create_profile(item) for item in defaults]
        return {
            "dry_run": False,
            "created": [item.conformance_profile_id for item in created],
            "profile_count": len(created),
        }


def _default_profiles(scope: list[str]) -> list[ConformanceProfileCreateRequest]:
    base_checks = [
        "required_contracts_present",
        "required_policy_actions_present",
        "input_schema_valid",
        "output_schema_valid",
        "no_activation_enabled",
        "no_code_loading",
        "no_external_source",
        "no_secret_schema",
        "no_domain_logic",
    ]
    specs = [
        ("generic_extension_metadata", "extension", ["manifest_valid", *base_checks]),
        ("generic_module_slot", "module_slot", base_checks),
        ("generic_capability_binding", "capability_binding", base_checks),
        (
            "high_risk_capability_binding",
            "capability_binding",
            [*base_checks, "sandbox_declared", "sandbox_profile_valid"],
        ),
        ("route_preview_safety", "route_preview", ["route_preview_safe", "no_activation_enabled"]),
        ("sandbox_required_binding", "sandbox", ["sandbox_declared", "sandbox_profile_valid"]),
    ]
    return [
        ConformanceProfileCreateRequest(
            name=name,
            description=f"Generic metadata-only conformance profile for {profile_type}.",
            profile_type=cast(Any, profile_type),
            owner_scope=scope,
            required_checks=cast(Any, checks),
            minimum_score=0.8,
            metadata={"seed": True},
        )
        for name, profile_type, checks in specs
    ]


__all__ = ["ConformanceProfileService"]
