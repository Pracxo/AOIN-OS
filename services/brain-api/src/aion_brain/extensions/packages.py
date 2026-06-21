"""Extension package metadata service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import AIONNotFoundException
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.extensions import (
    ExtensionArchiveRequest,
    ExtensionIntakeRequest,
    ExtensionPackage,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.extensions.hash import hash_manifest
from aion_brain.extensions.policy import authorize_extension_action
from aion_brain.extensions.repository import ExtensionRegistryRepository
from aion_brain.extensions.telemetry import emit_extension_telemetry


class ExtensionPackageService:
    """Create and read package metadata records."""

    def __init__(
        self,
        repository: ExtensionRegistryRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._settings = settings or get_settings()
        self._actor_context: ActorContext | None = None

    def with_actor_context(self, actor_context: ActorContext) -> ExtensionPackageService:
        clone = ExtensionPackageService(
            self._repository,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            settings=self._settings,
        )
        clone._actor_context = actor_context
        return clone

    def build_package(
        self,
        request: ExtensionIntakeRequest,
        *,
        status: str = "proposed",
        compatibility_status: str = "unknown",
        review_status: str = "not_reviewed",
    ) -> ExtensionPackage:
        """Build a package contract from an intake request without persisting it."""

        now = datetime.now(UTC)
        manifest = request.manifest
        return ExtensionPackage(
            extension_package_id=f"extension-package-{uuid4().hex}",
            trace_id=request.trace_id or self._trace_id(),
            actor_id=request.actor_id or self._actor_id(),
            workspace_id=request.workspace_id or self._workspace_id(),
            extension_key=manifest.extension_key,
            name=manifest.name,
            description=manifest.description,
            version=manifest.version,
            status=cast(Any, status),
            package_type=manifest.package_type,
            source_type=request.source_type,
            source_ref=request.source_ref,
            owner_scope=request.owner_scope,
            manifest_hash=hash_manifest(manifest.model_dump(mode="json")),
            manifest=manifest,
            declared_capabilities=manifest.declared_capabilities,
            declared_contracts=manifest.declared_contracts,
            declared_dependencies=manifest.declared_dependencies,
            declared_policy_actions=manifest.declared_policy_actions,
            declared_settings=manifest.declared_settings,
            declared_routes=manifest.declared_routes,
            declared_events=manifest.declared_events,
            declared_resources=manifest.declared_resources,
            compatibility_status=cast(Any, compatibility_status),
            review_status=cast(Any, review_status),
            metadata={
                "metadata_only": True,
                "source_ref_recorded": bool(request.source_ref),
                **request.metadata,
            },
            created_by=request.created_by or self._actor_id(),
            created_at=now,
            updated_at=now,
        )

    def save_package(self, package: ExtensionPackage) -> ExtensionPackage:
        """Persist package metadata after policy authorization."""

        authorize_extension_action(
            self._policy_adapter,
            "extension.package.create",
            package.owner_scope,
            actor_id=package.actor_id,
            workspace_id=package.workspace_id,
            trace_id=package.trace_id,
            resource_id=package.extension_package_id,
            risk_level="medium",
            context={"extension_key": package.extension_key, "version": package.version},
        )
        saved = self._repository.save_package(package)
        emit_extension_telemetry(
            self._telemetry_service,
            event_type="extension_package_registered",
            node_type="extension_package",
            node_id=saved.extension_package_id,
            scope=saved.owner_scope,
            intensity=0.6,
            payload={"extension_key": saved.extension_key, "status": saved.status},
        )
        return saved

    def get_package(self, extension_package_id: str, scope: list[str]) -> ExtensionPackage | None:
        authorize_extension_action(
            self._policy_adapter,
            "extension.package.read",
            scope,
            actor_id=self._actor_id(),
            workspace_id=self._workspace_id(),
            resource_id=extension_package_id,
            risk_level="low",
        )
        return self._repository.get_package(extension_package_id)

    def require_package(self, extension_package_id: str, scope: list[str]) -> ExtensionPackage:
        package = self.get_package(extension_package_id, scope)
        if package is None:
            raise AIONNotFoundException("extension_package_not_found")
        return package

    def list_packages(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        package_type: str | None = None,
        compatibility_status: str | None = None,
        review_status: str | None = None,
        include_deleted: bool = False,
        limit: int = 100,
    ) -> list[ExtensionPackage]:
        authorize_extension_action(
            self._policy_adapter,
            "extension.query",
            scope,
            actor_id=self._actor_id(),
            workspace_id=self._workspace_id(),
            resource_type="extension_registry",
            risk_level="low",
        )
        return self._repository.list_packages(
            status=status,
            package_type=package_type,
            compatibility_status=compatibility_status,
            review_status=review_status,
            include_deleted=include_deleted,
            limit=limit,
        )

    def archive(
        self,
        extension_package_id: str,
        scope: list[str],
        request: ExtensionArchiveRequest,
    ) -> ExtensionPackage:
        package = self.require_package(extension_package_id, scope)
        authorize_extension_action(
            self._policy_adapter,
            "extension.package.update",
            scope,
            actor_id=request.actor_id or self._actor_id(),
            workspace_id=self._workspace_id(),
            resource_id=extension_package_id,
            risk_level="medium",
            context={"reason": request.reason},
        )
        updated = package.model_copy(
            update={
                "status": "archived",
                "archived_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "metadata": {**package.metadata, "archive_reason": request.reason},
            }
        )
        return self._repository.save_package(updated)

    def soft_delete(
        self,
        extension_package_id: str,
        scope: list[str],
        actor_id: str | None = None,
    ) -> ExtensionPackage:
        package = self.require_package(extension_package_id, scope)
        authorize_extension_action(
            self._policy_adapter,
            "extension.package.delete",
            scope,
            actor_id=actor_id or self._actor_id(),
            workspace_id=self._workspace_id(),
            resource_id=extension_package_id,
            risk_level="medium",
        )
        updated = package.model_copy(
            update={
                "status": "deleted",
                "deleted_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            }
        )
        return self._repository.save_package(updated)

    def _actor_id(self) -> str | None:
        return self._actor_context.actor_id if self._actor_context else None

    def _workspace_id(self) -> str | None:
        return self._actor_context.workspace_id if self._actor_context else None

    def _trace_id(self) -> str | None:
        return self._actor_context.trace_id if self._actor_context else None


__all__ = ["ExtensionPackageService"]
