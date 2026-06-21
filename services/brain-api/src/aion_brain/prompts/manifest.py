"""Provider-neutral model input manifest service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.model_inputs import ModelInputManifest
from aion_brain.contracts.prompts import PromptBoundaryCheck, PromptPacket
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.prompts.audit import record_prompt_audit


class ModelInputManifestService:
    """Create and read provider-neutral model input manifests."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> ModelInputManifestService:
        return ModelInputManifestService(
            self._repository,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            audit_sink=self._audit_sink,
            actor_context=actor_context,
        )

    def create_from_packet(
        self,
        packet: PromptPacket,
        boundary_check: PromptBoundaryCheck | None,
    ) -> ModelInputManifest:
        """Create a manifest for a governed prompt packet."""

        authorize(
            self._policy_adapter,
            action_type="prompt.manifest.create",
            resource_type="model_input_manifest",
            resource_id=packet.prompt_packet_id,
            scope=packet.owner_scope,
            trace_id=packet.trace_id,
            actor_id=self._actor_context.actor_id or packet.actor_id,
            workspace_id=self._actor_context.workspace_id or packet.workspace_id,
            risk_level="medium",
        )
        safety_refs = []
        if boundary_check is not None:
            safety_refs.append(boundary_check.boundary_check_id)
            safety_refs.extend(
                finding.injection_finding_id for finding in boundary_check.injection_findings
            )
        status = "ready"
        if packet.status == "blocked" or (boundary_check is not None and not boundary_check.safe):
            status = "blocked"
        elif packet.status == "warning" or (boundary_check is not None and boundary_check.warnings):
            status = "warning"
        manifest = ModelInputManifest(
            model_input_manifest_id=f"model-input-manifest-{uuid4().hex}",
            trace_id=packet.trace_id,
            prompt_packet_id=packet.prompt_packet_id,
            model_route=packet.target_model_route,
            provider_type="generic",
            status=status,  # type: ignore[arg-type]
            input_hash=packet.rendered_hash,
            section_count=len(packet.section_manifests),
            token_estimate=packet.token_estimate,
            context_budget={
                "char_count": packet.char_count,
                "max_chars": packet.metadata.get("max_chars"),
            },
            grounding_refs=[ref for ref in [packet.grounding_verification_id] if ref],
            instruction_refs=[ref for ref in [packet.instruction_resolution_id] if ref],
            safety_refs=safety_refs,
            metadata={
                "packet_type": packet.packet_type,
                "status": packet.status,
                "provider_specific_content": False,
            },
            created_at=datetime.now(UTC),
        )
        save = getattr(self._repository, "save_manifest", None)
        stored = save(manifest) if callable(save) else manifest
        emit_telemetry(
            self._telemetry_service,
            event_type="model_input_manifest_created",
            node_type="model_input",
            node_id=stored.model_input_manifest_id,
            trace_id=stored.trace_id,
            intensity=0.55,
            payload={"status": stored.status, "prompt_packet_id": stored.prompt_packet_id},
        )
        record_prompt_audit(
            self._audit_sink,
            action_type="prompt.manifest.create",
            resource_type="model_input_manifest",
            resource_id=stored.model_input_manifest_id,
            event_type="model_input_manifest_created",
            trace_id=stored.trace_id,
            actor_context=self._actor_context,
            payload={"status": stored.status, "prompt_packet_id": stored.prompt_packet_id},
        )
        return stored

    def get_manifest(
        self, model_input_manifest_id: str, scope: list[str]
    ) -> ModelInputManifest | None:
        authorize(
            self._policy_adapter,
            action_type="prompt.manifest.read",
            resource_type="model_input_manifest",
            resource_id=model_input_manifest_id,
            scope=scope,
            trace_id=self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        get_manifest = getattr(self._repository, "get_manifest", None)
        result = get_manifest(model_input_manifest_id) if callable(get_manifest) else None
        return result if isinstance(result, ModelInputManifest) else None

    def list_manifests(
        self,
        scope: list[str],
        *,
        trace_id: str | None = None,
        prompt_packet_id: str | None = None,
        limit: int = 50,
    ) -> list[ModelInputManifest]:
        authorize(
            self._policy_adapter,
            action_type="prompt.manifest.read",
            resource_type="model_input_manifest",
            resource_id=prompt_packet_id or trace_id,
            scope=scope,
            trace_id=self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        list_manifests = getattr(self._repository, "list_manifests", None)
        if not callable(list_manifests):
            return []
        result = list_manifests(trace_id=trace_id, prompt_packet_id=prompt_packet_id, limit=limit)
        return [manifest for manifest in result if isinstance(manifest, ModelInputManifest)]


__all__ = ["ModelInputManifestService"]
