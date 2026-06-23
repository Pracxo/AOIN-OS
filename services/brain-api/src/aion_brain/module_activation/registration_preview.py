"""Runtime registration preview service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.api_support.errors import AIONNotFoundException
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.module_activation import RuntimeRegistrationPreview
from aion_brain.module_activation.policy import authorize_module_activation_action
from aion_brain.module_activation.repository import ModuleActivationRepository
from aion_brain.versioning.compatibility import emit_versioning_telemetry


class RuntimeRegistrationPreviewService:
    """Preview runtime registration without mutating runtime routing or config."""

    def __init__(
        self,
        repository: ModuleActivationRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._settings = settings or get_settings()

    def create_preview(
        self,
        activation_request_id: str,
        scope: list[str],
        *,
        created_by: str | None = None,
    ) -> RuntimeRegistrationPreview:
        if not self._settings.runtime_registration_preview_enabled:
            raise RuntimeError("runtime_registration_preview_disabled")
        request = self._repository.get_request(activation_request_id)
        if request is None or not _in_scope(request.owner_scope, scope):
            raise AIONNotFoundException("module_activation_request_not_found")
        authorize_module_activation_action(
            self._policy_adapter,
            "runtime.registration.preview.create",
            scope,
            actor_id=created_by or request.actor_id,
            workspace_id=request.workspace_id,
            trace_id=request.trace_id,
            resource_type="runtime_registration_preview",
            resource_id=activation_request_id,
            risk_level=request.risk_level,
            context={"registration_allowed": False, "runtime_mutation_allowed": False},
        )
        blockers = self._repository.list_blockers(
            activation_request_id=activation_request_id,
            status="open",
            limit=100,
        )
        preview = RuntimeRegistrationPreview(
            registration_preview_id=f"runtime-registration-preview-{uuid4().hex}",
            trace_id=request.trace_id,
            activation_request_id=request.activation_request_id,
            module_slot_id=request.module_slot_id,
            capability_binding_id=request.capability_binding_ids[0]
            if request.capability_binding_ids
            else None,
            status="blocked",
            preview_type="module_runtime",
            target_runtime="metadata_only",
            target_ref=request.module_slot_id,
            route_previews=[
                {
                    "route_key": f"module.{request.module_slot_id}",
                    "status": "not_registered",
                    "registration_allowed": False,
                }
            ],
            capability_previews=[
                {
                    "capability_binding_id": binding_id,
                    "status": "not_registered",
                    "activation_allowed": False,
                }
                for binding_id in request.capability_binding_ids
            ],
            policy_action_previews=[
                {"action_type": action, "status": "required"}
                for action in request.required_policy_actions
            ],
            setting_previews=[
                {"setting": setting, "status": "required"} for setting in request.required_settings
            ],
            would_register=False,
            registration_allowed=False,
            blockers=[blocker.model_dump(mode="json") for blocker in blockers],
            warnings=[
                {
                    "message": "Runtime registration is preview-only in AION-083.",
                    "runtime_mutation_allowed": False,
                }
            ],
            metadata={"metadata_only": True, "runtime_registration_enabled": False},
            created_by=created_by,
            created_at=datetime.now(UTC),
        )
        saved = self._repository.save_registration_preview(preview)
        self._repository.save_request(
            request.model_copy(
                update={
                    "registration_preview_id": saved.registration_preview_id,
                    "activation_allowed": False,
                    "execution_allowed": False,
                }
            )
        )
        self._emit("runtime_registration_preview_created", saved)
        return saved

    def get_preview(
        self,
        registration_preview_id: str,
        scope: list[str],
    ) -> RuntimeRegistrationPreview:
        authorize_module_activation_action(
            self._policy_adapter,
            "runtime.registration.preview.read",
            scope,
            resource_type="runtime_registration_preview",
            resource_id=registration_preview_id,
        )
        preview = self._repository.get_registration_preview(registration_preview_id)
        if preview is None:
            raise AIONNotFoundException("runtime_registration_preview_not_found")
        request = (
            self._repository.get_request(preview.activation_request_id)
            if preview.activation_request_id
            else None
        )
        if request is not None and not _in_scope(request.owner_scope, scope):
            raise AIONNotFoundException("runtime_registration_preview_not_found")
        return preview

    def list_previews(
        self,
        scope: list[str],
        *,
        activation_request_id: str | None = None,
        module_slot_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[RuntimeRegistrationPreview]:
        authorize_module_activation_action(
            self._policy_adapter,
            "runtime.registration.preview.read",
            scope,
            resource_type="runtime_registration_preview",
        )
        items = self._repository.list_registration_previews(
            activation_request_id=activation_request_id,
            module_slot_id=module_slot_id,
            status=status,
            limit=limit,
        )
        return [
            item
            for item in items
            if item.activation_request_id is None
            or _request_in_scope(self._repository, item.activation_request_id, scope)
        ]

    def _emit(self, event_type: str, preview: RuntimeRegistrationPreview) -> None:
        request = (
            self._repository.get_request(preview.activation_request_id)
            if preview.activation_request_id
            else None
        )
        emit_versioning_telemetry(
            self._telemetry_service,
            event_type=event_type,
            node_type="runtime_registration_preview",
            node_id=preview.registration_preview_id,
            intensity=0.5,
            scope=request.owner_scope if request else ["workspace:main"],
            payload={"registration_allowed": False, "status": preview.status},
        )


def _request_in_scope(
    repository: ModuleActivationRepository,
    activation_request_id: str,
    scope: list[str],
) -> bool:
    request = repository.get_request(activation_request_id)
    return request is not None and _in_scope(request.owner_scope, scope)


def _in_scope(owner_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(requested_scope))


__all__ = ["RuntimeRegistrationPreviewService"]
