"""Route binding preview service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import AIONNotFoundException
from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.capability_bindings import RouteBindingPreview, RoutePreviewCreateRequest
from aion_brain.module_bindings.policy import authorize_module_binding_action
from aion_brain.module_bindings.repository import ModuleBindingRepository
from aion_brain.module_bindings.telemetry import emit_module_binding_telemetry


class RouteBindingPreviewService:
    """Preview route metadata without dynamic registration."""

    def __init__(
        self,
        repository: ModuleBindingRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._settings = settings or get_settings()

    def create_preview(self, request: RoutePreviewCreateRequest) -> RouteBindingPreview:
        """Create one route binding preview."""

        if not self._settings.route_binding_preview_enabled:
            raise RuntimeError("route_binding_preview_disabled")
        binding = self._repository.get_binding(request.capability_binding_id)
        if binding is None:
            raise AIONNotFoundException("capability_binding_not_found")
        slot = self._repository.get_slot(binding.module_slot_id)
        scope = request.scope or (slot.owner_scope if slot else ["workspace:main"])
        authorize_module_binding_action(
            self._policy_adapter,
            "route_binding_preview.create",
            scope,
            actor_id=request.created_by,
            trace_id=binding.trace_id,
            resource_type="route_binding_preview",
            resource_id=request.capability_binding_id,
            risk_level="medium",
        )
        route_key = binding.route_key or binding.capability_key
        blockers = [
            {
                "code": "dynamic_route_registration_disabled",
                "severity": "high",
                "message": "Dynamic route registration is disabled in v0.1.",
            }
        ]
        preview = RouteBindingPreview(
            route_preview_id=f"route-binding-preview-{uuid4().hex}",
            trace_id=binding.trace_id,
            module_slot_id=binding.module_slot_id,
            capability_binding_id=binding.capability_binding_id,
            status="blocked",
            route_key=route_key,
            route_type=cast(Any, binding.metadata.get("route_type") or "generic"),
            method=cast(str | None, binding.metadata.get("method")),
            path=cast(str | None, binding.metadata.get("path")),
            target_runtime=binding.target_runtime,
            target_ref=binding.target_ref,
            would_register=bool(binding.route_key),
            registration_allowed=False,
            blockers=blockers,
            warnings=[
                {
                    "code": "preview_only",
                    "severity": "medium",
                    "message": "This record previews route shape only.",
                }
            ],
            metadata={
                "metadata_only": True,
                "source_records_mutated": False,
                "dynamic_route_registration_allowed": False,
            },
            created_by=request.created_by,
            created_at=datetime.now(UTC),
        )
        saved = self._repository.save_route_preview(preview)
        self._record_audit(saved)
        emit_module_binding_telemetry(
            self._telemetry_service,
            event_type="route_binding_preview_created",
            node_type="route_binding_preview",
            node_id=saved.route_preview_id,
            scope=scope,
            intensity=0.5,
            payload={"route_key": saved.route_key, "registration_allowed": False},
        )
        return saved

    def list_previews(
        self,
        scope: list[str],
        *,
        module_slot_id: str | None = None,
        capability_binding_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[RouteBindingPreview]:
        """List route binding previews."""

        authorize_module_binding_action(
            self._policy_adapter,
            "route_binding_preview.read",
            scope,
            resource_type="route_binding_preview",
            risk_level="low",
        )
        return self._repository.list_route_previews(
            module_slot_id=module_slot_id,
            capability_binding_id=capability_binding_id,
            status=status,
            limit=limit,
        )

    def _record_audit(self, preview: RouteBindingPreview) -> None:
        record_audit_event(
            self._audit_sink,
            action_type="route_binding_preview.create",
            resource_type="route_binding_preview",
            resource_id=preview.route_preview_id,
            event_type="route_binding_preview_created",
            outcome="blocked",
            source_component="module_binding_registry",
            trace_id=preview.trace_id,
            risk_level="medium",
            payload={"route_key": preview.route_key, "metadata_only": True},
        )


__all__ = ["RouteBindingPreviewService"]
