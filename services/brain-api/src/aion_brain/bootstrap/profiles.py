"""Bootstrap profile catalog."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from aion_brain.api_support.errors import AIONNotFoundException
from aion_brain.bootstrap.policy import authorize_bootstrap_action
from aion_brain.bootstrap.repository import BootstrapRepository
from aion_brain.bootstrap.telemetry import emit_bootstrap_telemetry
from aion_brain.contracts.bootstrap import BootstrapProfile


class BootstrapProfileService:
    """Manage local first-run bootstrap profiles."""

    def __init__(
        self,
        repository: BootstrapRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def create_profile(self, profile: BootstrapProfile) -> BootstrapProfile:
        """Create or replace a bootstrap profile."""
        authorize_bootstrap_action(
            self._policy_adapter,
            "bootstrap.profile.create",
            profile.owner_scope,
            actor_id=profile.created_by,
            resource_type="bootstrap_profile",
            resource_id=profile.profile_key,
            risk_level="medium",
            context={"external_calls": False, "production_profile": False},
        )
        now = datetime.now(UTC)
        saved = self._repository.save_profile(
            profile.model_copy(update={"created_at": profile.created_at or now, "updated_at": now})
        )
        emit_bootstrap_telemetry(
            self._telemetry_service,
            event_type="bootstrap_profile_created",
            node_type="bootstrap_profile",
            node_id=saved.bootstrap_profile_id,
            scope=saved.owner_scope,
            intensity=0.4,
            payload={"profile_key": saved.profile_key, "profile_type": saved.profile_type},
        )
        return saved

    def get_profile(self, profile_key: str, scope: list[str]) -> BootstrapProfile | None:
        """Return one bootstrap profile."""
        authorize_bootstrap_action(
            self._policy_adapter,
            "bootstrap.profile.read",
            scope,
            resource_type="bootstrap_profile",
            resource_id=profile_key,
        )
        return self._repository.get_profile(profile_key) or _default_profile_by_key(
            profile_key, scope
        )

    def list_profiles(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        profile_type: str | None = None,
        limit: int = 100,
    ) -> list[BootstrapProfile]:
        """List persisted profiles plus built-in defaults."""
        authorize_bootstrap_action(
            self._policy_adapter,
            "bootstrap.profile.read",
            scope,
            resource_type="bootstrap_profile",
        )
        persisted = self._repository.list_profiles(
            status=status,
            profile_type=profile_type,
            limit=limit,
        )
        existing = {item.profile_key for item in persisted}
        defaults = [item for item in default_profiles(scope) if item.profile_key not in existing]
        profiles = [*persisted, *defaults]
        if status is not None:
            profiles = [item for item in profiles if item.status == status]
        if profile_type is not None:
            profiles = [item for item in profiles if item.profile_type == profile_type]
        return profiles[:limit]

    def disable_profile(
        self,
        profile_key: str,
        actor_id: str | None,
        reason: str,
        scope: list[str],
    ) -> BootstrapProfile:
        """Disable a bootstrap profile."""
        authorize_bootstrap_action(
            self._policy_adapter,
            "bootstrap.profile.update",
            scope,
            actor_id=actor_id,
            resource_type="bootstrap_profile",
            resource_id=profile_key,
            risk_level="medium",
            context={"reason": reason, "external_calls": False},
        )
        profile = self._repository.disable_profile(profile_key)
        if profile is None:
            raise AIONNotFoundException("bootstrap_profile_not_found")
        return profile

    def seed_default_profiles(
        self,
        scope: list[str],
        dry_run: bool = True,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        """Seed built-in local bootstrap profiles."""
        authorize_bootstrap_action(
            self._policy_adapter,
            "bootstrap.profile.create",
            scope,
            actor_id=created_by,
            risk_level="medium",
            context={"dry_run": dry_run, "default_profiles": True, "external_calls": False},
        )
        profiles = default_profiles(scope, created_by=created_by)
        if dry_run:
            return {
                "dry_run": True,
                "created": [],
                "profiles": [item.model_dump(mode="json") for item in profiles],
            }
        created = [self.create_profile(profile) for profile in profiles]
        return {
            "dry_run": False,
            "created": [item.bootstrap_profile_id for item in created],
            "profiles": [item.model_dump(mode="json") for item in created],
        }


def default_profiles(scope: list[str], *, created_by: str | None = None) -> list[BootstrapProfile]:
    """Return v0.1 built-in local profiles."""
    specs: list[tuple[str, str, str, str, list[str], list[str]]] = [
        (
            "local.dev",
            "Local Developer",
            "Prepare a safe local developer Brain environment.",
            "local_dev",
            ["postgres", "redis", "nats", "opa", "brain_api"],
            ["core.defaults", "operator.defaults", "local.dev.defaults"],
        ),
        (
            "local.docker",
            "Local Docker",
            "Inspect the local Docker-backed Brain stack.",
            "docker_local",
            ["postgres", "redis", "nats", "opa", "brain_api"],
            ["core.defaults", "registry.defaults", "contract.defaults"],
        ),
        (
            "local.golden_path",
            "Local Golden Path",
            "Prepare deterministic golden path readiness checks.",
            "golden_path",
            ["brain_api", "opa"],
            ["golden_path.defaults"],
        ),
        (
            "local.release_candidate",
            "Local Release Candidate",
            "Inspect local release readiness without deployment.",
            "release_candidate",
            ["brain_api", "opa"],
            ["core.defaults", "golden_path.defaults", "local.dev.defaults"],
        ),
    ]
    now = datetime.now(UTC)
    return [
        BootstrapProfile(
            bootstrap_profile_id=f"bootstrap-profile-{key.replace('.', '-')}",
            profile_key=key,
            name=name,
            description=description,
            status="active",
            profile_type=cast(Any, profile_type),
            owner_scope=scope,
            required_services=services,
            required_settings=[
                "AION_BOOTSTRAP_ENABLED",
                "AION_SETUP_DOCTOR_ENABLED",
                "AION_SEED_BUNDLES_ENABLED",
            ],
            seed_bundle_keys=bundles,
            checks=[
                "health",
                "policy",
                "sdk",
                "cli",
                "scripts",
                "golden_path",
                "release_smoke",
            ],
            constraints=[
                "local_only",
                "dry_run_default",
                "no_external_calls",
                "no_package_install",
                "no_production_secrets",
            ],
            metadata={"source": "default_bootstrap_profile"},
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )
        for key, name, description, profile_type, services, bundles in specs
    ]


def _default_profile_by_key(profile_key: str, scope: list[str]) -> BootstrapProfile | None:
    for profile in default_profiles(scope):
        if profile.profile_key == profile_key:
            return profile
    return None


__all__ = ["BootstrapProfileService", "default_profiles"]
