"""Seed bundle catalog."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from aion_brain.api_support.errors import AIONNotFoundException
from aion_brain.bootstrap.policy import authorize_bootstrap_action
from aion_brain.bootstrap.repository import BootstrapRepository
from aion_brain.bootstrap.telemetry import emit_bootstrap_telemetry
from aion_brain.contracts.bootstrap import SeedBundle


class SeedBundleService:
    """Manage idempotent local seed bundle metadata."""

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

    def create_bundle(self, bundle: SeedBundle) -> SeedBundle:
        """Create or replace a seed bundle."""
        authorize_bootstrap_action(
            self._policy_adapter,
            "bootstrap.seed_bundle.create",
            bundle.owner_scope,
            actor_id=bundle.created_by,
            resource_type="seed_bundle",
            resource_id=bundle.seed_bundle_key,
            risk_level="medium",
            context={"external_calls": False, "idempotent": True},
        )
        now = datetime.now(UTC)
        saved = self._repository.save_bundle(
            bundle.model_copy(update={"created_at": bundle.created_at or now, "updated_at": now})
        )
        emit_bootstrap_telemetry(
            self._telemetry_service,
            event_type="seed_bundle_created",
            node_type="seed_bundle",
            node_id=saved.seed_bundle_id,
            scope=saved.owner_scope,
            intensity=0.4,
            payload={"seed_bundle_key": saved.seed_bundle_key, "bundle_type": saved.bundle_type},
        )
        return saved

    def get_bundle(self, seed_bundle_key: str, scope: list[str]) -> SeedBundle | None:
        """Return one seed bundle."""
        authorize_bootstrap_action(
            self._policy_adapter,
            "bootstrap.seed_bundle.read",
            scope,
            resource_type="seed_bundle",
            resource_id=seed_bundle_key,
        )
        return self._repository.get_bundle(seed_bundle_key) or _default_bundle_by_key(
            seed_bundle_key, scope
        )

    def list_bundles(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        bundle_type: str | None = None,
        limit: int = 100,
    ) -> list[SeedBundle]:
        """List persisted bundles plus built-in defaults."""
        authorize_bootstrap_action(
            self._policy_adapter,
            "bootstrap.seed_bundle.read",
            scope,
            resource_type="seed_bundle",
        )
        persisted = self._repository.list_bundles(
            status=status,
            bundle_type=bundle_type,
            limit=limit,
        )
        existing = {item.seed_bundle_key for item in persisted}
        defaults = [
            item for item in default_seed_bundles(scope) if item.seed_bundle_key not in existing
        ]
        bundles = [*persisted, *defaults]
        if status is not None:
            bundles = [item for item in bundles if item.status == status]
        if bundle_type is not None:
            bundles = [item for item in bundles if item.bundle_type == bundle_type]
        return bundles[:limit]

    def disable_bundle(
        self,
        seed_bundle_key: str,
        actor_id: str | None,
        reason: str,
        scope: list[str],
    ) -> SeedBundle:
        """Disable a seed bundle."""
        authorize_bootstrap_action(
            self._policy_adapter,
            "bootstrap.seed_bundle.update",
            scope,
            actor_id=actor_id,
            resource_type="seed_bundle",
            resource_id=seed_bundle_key,
            risk_level="medium",
            context={"reason": reason, "external_calls": False},
        )
        bundle = self._repository.disable_bundle(seed_bundle_key)
        if bundle is None:
            raise AIONNotFoundException("seed_bundle_not_found")
        return bundle

    def seed_default_bundles(
        self,
        scope: list[str],
        dry_run: bool = True,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        """Seed built-in local seed bundles."""
        authorize_bootstrap_action(
            self._policy_adapter,
            "bootstrap.seed_bundle.create",
            scope,
            actor_id=created_by,
            risk_level="medium",
            context={"dry_run": dry_run, "default_bundles": True, "external_calls": False},
        )
        bundles = default_seed_bundles(scope, created_by=created_by)
        if dry_run:
            return {
                "dry_run": True,
                "created": [],
                "seed_bundles": [item.model_dump(mode="json") for item in bundles],
            }
        created = [self.create_bundle(bundle) for bundle in bundles]
        return {
            "dry_run": False,
            "created": [item.seed_bundle_id for item in created],
            "seed_bundles": [item.model_dump(mode="json") for item in created],
        }


def default_seed_bundles(scope: list[str], *, created_by: str | None = None) -> list[SeedBundle]:
    """Return v0.1 built-in seed bundles."""
    specs: list[tuple[str, str, str, str, list[str]]] = [
        (
            "core.defaults",
            "Core Defaults",
            "Seed local core metadata.",
            "core_defaults",
            ["kernel", "policy"],
        ),
        (
            "operator.defaults",
            "Operator Defaults",
            "Seed local operator metadata.",
            "operator_defaults",
            ["operator"],
        ),
        (
            "notification.defaults",
            "Notification Defaults",
            "Seed local notification defaults.",
            "notification_defaults",
            ["notifications"],
        ),
        (
            "registry.defaults",
            "Registry Defaults",
            "Seed local registry defaults.",
            "registry_defaults",
            ["registry"],
        ),
        (
            "contract.defaults",
            "Contract Defaults",
            "Seed local contract defaults.",
            "contract_defaults",
            ["contract_registry"],
        ),
        (
            "lifecycle.defaults",
            "Lifecycle Defaults",
            "Seed local lifecycle defaults.",
            "lifecycle_defaults",
            ["lifecycle"],
        ),
        (
            "extension.defaults",
            "Extension Defaults",
            "Seed local extension defaults.",
            "extension_defaults",
            ["extensions"],
        ),
        (
            "conformance.defaults",
            "Conformance Defaults",
            "Seed local conformance defaults.",
            "conformance_defaults",
            ["conformance"],
        ),
        (
            "golden_path.defaults",
            "Golden Path Defaults",
            "Seed local golden path defaults.",
            "golden_path_defaults",
            ["golden_path_scenarios", "golden_path_fixtures"],
        ),
        (
            "local.dev.defaults",
            "Local Developer Defaults",
            "Seed local developer defaults.",
            "local_dev",
            ["self_model", "limitations"],
        ),
    ]
    now = datetime.now(UTC)
    bundles: list[SeedBundle] = []
    for key, name, description, bundle_type, service_keys in specs:
        seed_steps = [
            {
                "step_key": f"{key}.{service_key}",
                "service_key": service_key,
                "idempotency_key": f"{key}.{service_key}",
                "mode": "metadata_default",
                "external_calls": False,
            }
            for service_key in service_keys
        ]
        bundles.append(
            SeedBundle(
                seed_bundle_id=f"seed-bundle-{key.replace('.', '-')}",
                seed_bundle_key=key,
                name=name,
                description=description,
                status="active",
                bundle_type=cast(Any, bundle_type),
                owner_scope=scope,
                seed_steps=seed_steps,
                idempotency_keys=[str(step["idempotency_key"]) for step in seed_steps],
                dependencies=[],
                metadata={"source": "default_seed_bundle", "idempotent": True},
                created_by=created_by,
                created_at=now,
                updated_at=now,
            )
        )
    return bundles


def _default_bundle_by_key(seed_bundle_key: str, scope: list[str]) -> SeedBundle | None:
    for bundle in default_seed_bundles(scope):
        if bundle.seed_bundle_key == seed_bundle_key:
            return bundle
    return None


__all__ = ["SeedBundleService", "default_seed_bundles"]
