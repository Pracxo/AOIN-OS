"""Self-model profile service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from aion_brain.contracts.self_model import (
    SelfDescription,
    SelfDescriptionRequest,
    SelfModelProfile,
)
from aion_brain.outcomes._shared import authorize, emit_telemetry, scope_matches
from aion_brain.self_model.defaults import default_profile
from aion_brain.self_model.repository import SelfModelRepository


class SelfModelProfileService:
    """Read and update AION's factual self-model profile."""

    def __init__(
        self,
        repository: SelfModelRepository,
        policy_adapter: object,
        *,
        capability_awareness_service: object | None = None,
        limitation_service: object | None = None,
        settings: object | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._capability_awareness_service = capability_awareness_service
        self._limitation_service = limitation_service
        self._settings = settings
        self._telemetry_service = telemetry_service

    def get_active_profile(self, scope: list[str]) -> SelfModelProfile:
        authorize(
            self._policy_adapter,
            action_type="self_model.read",
            resource_type="self_model",
            resource_id="active",
            scope=scope,
            risk_level="low",
        )
        stored = self._repository.get_active_profile()
        if stored is not None and scope_matches(stored.owner_scope, scope):
            return stored
        return default_profile(self._settings or object(), scope)

    def create_or_update_profile(self, profile: SelfModelProfile) -> SelfModelProfile:
        authorize(
            self._policy_adapter,
            action_type="self_model.update",
            resource_type="self_model",
            resource_id=profile.self_model_id,
            scope=profile.owner_scope,
            risk_level="low",
            context={"status": profile.status},
        )
        now = datetime.now(UTC)
        return self._repository.save_profile(
            profile.model_copy(update={"updated_at": now, "created_at": profile.created_at or now})
        )

    def describe(self, request: SelfDescriptionRequest) -> SelfDescription:
        authorize(
            self._policy_adapter,
            action_type="self_model.describe",
            resource_type="self_model",
            resource_id="aion",
            scope=request.scope,
            risk_level="low",
            context={"format": request.format},
        )
        profile = self.get_active_profile(request.scope)
        capabilities = []
        if request.include_capabilities:
            list_capabilities = getattr(
                self._capability_awareness_service, "list_capabilities", None
            )
            if callable(list_capabilities):
                capabilities = list_capabilities(request.scope)
        limitations = []
        if request.include_limitations:
            list_limitations = getattr(self._limitation_service, "list_limitations", None)
            if callable(list_limitations):
                limitations = list_limitations(
                    request.scope,
                    status="active",
                    disclosure_required=True,
                )
        disabled_count = sum(1 for item in capabilities if item.status != "active")
        disclosures = [
            "AION v0.1 self model is descriptive and diagnostic.",
            "AION does not claim sentience, production readiness, or full autonomy.",
        ]
        disclosures.extend(item.limitation_key for item in limitations if item.disclosure_required)
        description = SelfDescription(
            name=profile.name,
            full_name=profile.full_name,
            version=profile.version,
            summary=(
                f"{profile.name} ({profile.full_name}) is a governed Brain operating system "
                "with descriptive awareness of configured capabilities and limitations."
            ),
            architecture=profile.architecture_refs if request.include_architecture else [],
            capabilities=capabilities,
            limitations=limitations,
            status={
                "profile_status": profile.status,
                "capability_count": len(capabilities),
                "disabled_or_unavailable_capability_count": disabled_count,
                "limitation_count": len(limitations),
                "format": request.format,
            }
            if request.include_status
            else {},
            disclosures=disclosures,
            generated_at=datetime.now(UTC),
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="self_description_generated",
            node_type="self_model",
            node_id="aion",
            intensity=0.5,
            trace_id=None,
            payload={
                "owner_scope": request.scope,
                "capability_count": len(capabilities),
                "limitation_count": len(limitations),
            },
        )
        return description

    def status(self, scope: list[str] | None = None) -> dict[str, Any]:
        profile = self.get_active_profile(scope or ["workspace:main"])
        return {
            "status": "healthy" if profile.status == "active" else "warning",
            "name": profile.name,
            "version": profile.version,
            "official_full_name": profile.full_name,
        }
