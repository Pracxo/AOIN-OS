"""Golden path synthetic fixture packs."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.config import Settings, get_settings
from aion_brain.contracts.golden_path import GoldenPathFixturePack
from aion_brain.golden_path.policy import authorize_golden_path_action
from aion_brain.golden_path.repository import GoldenPathRepository
from aion_brain.golden_path.telemetry import emit_golden_path_telemetry


class FixturePackService:
    """Manage synthetic fixture packs for dry-run golden paths."""

    def __init__(
        self,
        repository: GoldenPathRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._settings = settings or get_settings()

    def seed_default_fixture_packs(
        self,
        scope: list[str],
        dry_run: bool = True,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        """Seed synthetic default fixture packs."""
        if not self._settings.golden_path_fixture_seeding_enabled:
            return {"dry_run": dry_run, "created": [], "fixtures": [], "status": "disabled"}
        authorize_golden_path_action(
            self._policy_adapter,
            "golden_path.fixture.create",
            scope,
            actor_id=created_by,
            risk_level="medium",
            context={"dry_run": dry_run, "synthetic": True},
        )
        packs = default_fixture_packs(scope, self._settings.golden_path_workspace_id_default)
        if dry_run:
            return {
                "dry_run": True,
                "created": [],
                "fixtures": [pack.model_dump(mode="json") for pack in packs],
            }
        created = [self.create_fixture_pack(pack) for pack in packs]
        return {
            "dry_run": False,
            "created": [pack.fixture_pack_id for pack in created],
            "fixtures": [pack.model_dump(mode="json") for pack in created],
        }

    def create_fixture_pack(self, pack: GoldenPathFixturePack) -> GoldenPathFixturePack:
        """Create a fixture pack."""
        authorize_golden_path_action(
            self._policy_adapter,
            "golden_path.fixture.create",
            pack.owner_scope,
            actor_id=pack.created_by,
            resource_type="golden_path_fixture",
            resource_id=pack.fixture_pack_key,
            risk_level="medium",
            context={"synthetic": True, "external_calls": False},
        )
        now = datetime.now(UTC)
        saved = self._repository.save_fixture_pack(
            pack.model_copy(update={"created_at": pack.created_at or now})
        )
        emit_golden_path_telemetry(
            self._telemetry_service,
            event_type="golden_path_fixture_pack_created",
            node_type="golden_path_fixture",
            node_id=saved.fixture_pack_id,
            scope=saved.owner_scope,
            intensity=0.4,
            payload={"fixture_pack_key": saved.fixture_pack_key},
        )
        return saved

    def list_fixture_packs(
        self,
        scope: list[str],
        status: str | None = None,
        limit: int = 100,
    ) -> list[GoldenPathFixturePack]:
        """List fixture packs."""
        authorize_golden_path_action(
            self._policy_adapter,
            "golden_path.fixture.read",
            scope,
            resource_type="golden_path_fixture",
        )
        return self._repository.list_fixture_packs(status=status, limit=limit)

    def get_fixture_pack(
        self,
        fixture_pack_key: str,
        scope: list[str],
    ) -> GoldenPathFixturePack | None:
        """Return one fixture pack by key."""
        authorize_golden_path_action(
            self._policy_adapter,
            "golden_path.fixture.read",
            scope,
            resource_type="golden_path_fixture",
            resource_id=fixture_pack_key,
        )
        return self._repository.get_fixture_pack(fixture_pack_key)


def default_fixture_packs(scope: list[str], workspace_id: str) -> list[GoldenPathFixturePack]:
    """Return default synthetic fixture packs."""
    return [
        _pack(
            "golden.core",
            "Core Fixtures",
            "Synthetic core boot and identity fixtures.",
            scope,
            workspace_id,
        ),
        _pack(
            "golden.dialogue",
            "Dialogue Fixtures",
            "Synthetic dialogue and prompt fixtures.",
            scope,
            workspace_id,
        ),
        _pack(
            "golden.action",
            "Action Fixtures",
            "Synthetic action proposal and handoff fixtures.",
            scope,
            workspace_id,
        ),
        _pack(
            "golden.operations",
            "Operations Fixtures",
            "Synthetic scheduler, alert, and incident fixtures.",
            scope,
            workspace_id,
        ),
        _pack(
            "golden.registry",
            "Registry Fixtures",
            "Synthetic registry and lifecycle fixtures.",
            scope,
            workspace_id,
        ),
        _pack(
            "golden.extension",
            "Extension Fixtures",
            "Synthetic extension, binding, and conformance fixtures.",
            scope,
            workspace_id,
        ),
    ]


def _pack(
    key: str,
    name: str,
    description: str,
    scope: list[str],
    workspace_id: str,
) -> GoldenPathFixturePack:
    return GoldenPathFixturePack(
        fixture_pack_id=f"fixture-pack-{key.replace('.', '-')}",
        fixture_pack_key=key,
        name=name,
        description=description,
        status="active",
        owner_scope=scope,
        workspace_id=workspace_id,
        fixtures=[
            {
                "fixture_id": f"{key}.synthetic",
                "synthetic": True,
                "summary": description,
                "external_reference": False,
            }
        ],
        seeded_resource_refs=[f"aion://golden_path_fixture/{key}"],
        metadata={"default": True, "scenario_owned": True, "created_marker": uuid4().hex[:8]},
    )


__all__ = ["FixturePackService", "default_fixture_packs"]
