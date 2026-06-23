"""Prompt packet compiler and context boundary guard."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.contracts.model_inputs import ModelInputManifest
from aion_brain.contracts.prompts import (
    PromptBoundaryCheck,
    PromptCompileRequest,
    PromptCompileResult,
    PromptPacket,
    PromptPacketStatus,
    PromptSection,
    PromptTemplate,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.prompts.audit import create_prompt_provenance_link, record_prompt_audit
from aion_brain.prompts.hash import hash_prompt_sections
from aion_brain.prompts.redaction import redact_prompt_section
from aion_brain.prompts.sectioner import PromptSectioner, order_sections, trim_sections


class PromptPacketCompiler:
    """Compile governed, provider-neutral prompt packets."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        sectioner: PromptSectioner | None = None,
        boundary_checker: object | None = None,
        manifest_service: object | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
        autonomy_governor: object | None = None,
        settings: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._sectioner = sectioner or PromptSectioner()
        self._boundary_checker = boundary_checker
        self._manifest_service = manifest_service
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service
        self._autonomy_governor = autonomy_governor
        self._settings = settings
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> PromptPacketCompiler:
        """Return a request-scoped compiler wrapper."""

        return PromptPacketCompiler(
            self._repository,
            self._policy_adapter,
            sectioner=self._sectioner,
            boundary_checker=self._boundary_checker,
            manifest_service=self._manifest_service,
            telemetry_service=self._telemetry_service,
            audit_sink=self._audit_sink,
            provenance_service=self._provenance_service,
            autonomy_governor=self._autonomy_governor,
            settings=self._settings,
            actor_context=actor_context,
        )

    def build_egress_preview_metadata(self, packet: PromptPacket) -> dict[str, Any]:
        """Return redacted prompt metadata for provider egress previews only."""

        return {
            "prompt_packet_ref": packet.prompt_packet_id,
            "section_count": len(packet.sections),
            "token_estimate": packet.token_estimate,
            "char_count": packet.char_count,
            "rendered_hash": packet.rendered_hash,
            "raw_prompt_included": False,
            "hidden_reasoning_included": False,
        }

    def compile(self, request: PromptCompileRequest) -> PromptCompileResult:
        """Compile a prompt packet without provider-specific rendering."""

        if self._settings is not None and (
            not bool(getattr(self._settings, "prompts_enabled", True))
            or not bool(getattr(self._settings, "prompt_compiler_enabled", True))
        ):
            raise RuntimeError("prompt_compiler_disabled")
        authorize(
            self._policy_adapter,
            action_type="prompt.compile",
            resource_type="prompt_packet",
            resource_id=request.prompt_packet_id,
            scope=request.owner_scope,
            trace_id=request.trace_id or self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id or request.actor_id,
            workspace_id=self._actor_context.workspace_id or request.workspace_id,
            risk_level="medium",
            context={
                "packet_type": request.packet_type,
                "target_model_route": request.target_model_route,
            },
        )
        prompt_packet_id = request.prompt_packet_id or f"prompt-packet-{uuid4().hex}"
        template = self._load_template(request.prompt_template_id, request.owner_scope)
        sections = []
        if template is not None:
            sections.extend(template.sections)
        sections.extend(self._sectioner.build_sections(request))
        sections = [
            redact_prompt_section(section)
            for section in trim_sections(order_sections(sections), request.max_chars)
        ]
        rendered_hash = hash_prompt_sections(sections)
        char_count = sum(len(section.content) for section in sections)
        token_estimate = _estimate_tokens(char_count)
        metadata = {
            **request.metadata,
            "max_chars": request.max_chars,
            "section_count": len(sections),
            "provider_specific_content": False,
        }
        boundary_check = self._check_boundary(
            sections,
            scope=request.owner_scope,
            trace_id=request.trace_id or self._actor_context.trace_id,
            prompt_packet_id=prompt_packet_id,
            created_by=request.created_by or self._actor_context.actor_id,
        )
        status = _packet_status(boundary_check)
        packet = PromptPacket(
            prompt_packet_id=prompt_packet_id,
            trace_id=request.trace_id or self._actor_context.trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            status=status,
            packet_type=request.packet_type,
            prompt_template_id=request.prompt_template_id,
            target_model_route=request.target_model_route,
            owner_scope=request.owner_scope,
            input_refs=_input_refs(request),
            sections=sections,
            section_manifests=[_section_manifest(section) for section in sections],
            rendered_hash=rendered_hash,
            redacted_preview=_preview(sections) if request.include_redacted_preview else None,
            token_estimate=token_estimate,
            char_count=char_count,
            boundary_check_id=boundary_check.boundary_check_id if boundary_check else None,
            grounding_verification_id=request.grounding_verification_id,
            instruction_resolution_id=request.instruction_resolution_id,
            constraints=sorted(
                set((boundary_check.constraints if boundary_check else []) + ["provider_neutral"])
            ),
            metadata=metadata,
            created_by=request.created_by or self._actor_context.actor_id,
            created_at=datetime.now(UTC),
        )
        stored_packet = self._save_packet_if_requested(packet, request)
        manifest = self._create_manifest(stored_packet, boundary_check)
        emit_telemetry(
            self._telemetry_service,
            event_type="prompt_packet_compiled",
            node_type="prompt_packet",
            node_id=stored_packet.prompt_packet_id,
            trace_id=stored_packet.trace_id,
            intensity=0.75 if stored_packet.status != "blocked" else 0.95,
            payload={"status": stored_packet.status, "section_count": len(stored_packet.sections)},
        )
        audit_entry_id = record_prompt_audit(
            self._audit_sink,
            action_type="prompt.compile",
            resource_type="prompt_packet",
            resource_id=stored_packet.prompt_packet_id,
            event_type="prompt_packet_compiled",
            trace_id=stored_packet.trace_id,
            actor_context=self._actor_context,
            payload={
                "status": stored_packet.status,
                "rendered_hash": stored_packet.rendered_hash,
                "token_estimate": stored_packet.token_estimate,
            },
            outcome="blocked" if stored_packet.status == "blocked" else "completed",
        )
        create_prompt_provenance_link(
            self._provenance_service,
            source_type="prompt_template",
            source_id=request.prompt_template_id,
            target_type="prompt_packet",
            target_id=stored_packet.prompt_packet_id,
            trace_id=stored_packet.trace_id,
            relation_type="produced",
            audit_entry_id=audit_entry_id,
        )
        return PromptCompileResult(
            prompt_packet=stored_packet,
            boundary_check=boundary_check,
            model_input_manifest=manifest,
            blocked=stored_packet.status == "blocked",
            constraints=stored_packet.constraints,
            warnings=boundary_check.warnings if boundary_check else [],
            created_at=datetime.now(UTC),
        )

    def get_packet(self, prompt_packet_id: str, scope: list[str]) -> PromptPacket | None:
        """Return one packet without restored raw section content."""

        authorize(
            self._policy_adapter,
            action_type="prompt.packet.read",
            resource_type="prompt_packet",
            resource_id=prompt_packet_id,
            scope=scope,
            trace_id=self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        get_packet = getattr(self._repository, "get_packet", None)
        packet = get_packet(prompt_packet_id) if callable(get_packet) else None
        if not isinstance(packet, PromptPacket):
            return None
        if not _scope_matches(packet.owner_scope, scope):
            return None
        return packet

    def list_packets(
        self,
        scope: list[str],
        *,
        trace_id: str | None = None,
        status: str | None = None,
        packet_type: str | None = None,
        limit: int = 50,
    ) -> list[PromptPacket]:
        """List visible packet metadata."""

        authorize(
            self._policy_adapter,
            action_type="prompt.packet.read",
            resource_type="prompt_packet",
            resource_id=trace_id,
            scope=scope,
            trace_id=self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        list_packets = getattr(self._repository, "list_packets", None)
        if not callable(list_packets):
            return []
        result = list_packets(
            scope,
            trace_id=trace_id,
            status=status,
            packet_type=packet_type,
            limit=limit,
        )
        return [packet for packet in result if isinstance(packet, PromptPacket)]

    def delete_packet(self, prompt_packet_id: str, scope: list[str]) -> dict[str, object]:
        """Soft-delete support placeholder for prompt packet records."""

        authorize(
            self._policy_adapter,
            action_type="prompt.packet.delete",
            resource_type="prompt_packet",
            resource_id=prompt_packet_id,
            scope=scope,
            trace_id=self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="medium",
        )
        delete = getattr(self._repository, "delete_packet", None)
        deleted = bool(delete(prompt_packet_id) if callable(delete) else False)
        return {"deleted": deleted, "prompt_packet_id": prompt_packet_id}

    def _load_template(
        self, prompt_template_id: str | None, scope: list[str]
    ) -> PromptTemplate | None:
        if not prompt_template_id:
            return None
        get_template = getattr(self._repository, "get_template", None)
        result = get_template(prompt_template_id) if callable(get_template) else None
        if isinstance(result, PromptTemplate) and _scope_matches(result.owner_scope, scope):
            return result
        return None

    def _check_boundary(
        self,
        sections: list[PromptSection],
        *,
        scope: list[str],
        trace_id: str | None,
        prompt_packet_id: str,
        created_by: str | None,
    ) -> PromptBoundaryCheck | None:
        if self._settings is not None and not bool(
            getattr(self._settings, "prompt_boundary_enabled", True)
        ):
            return None
        check_sections = getattr(self._boundary_checker, "check_sections", None)
        if callable(check_sections):
            result = check_sections(
                sections,
                scope=scope,
                trace_id=trace_id,
                prompt_packet_id=prompt_packet_id,
                created_by=created_by,
            )
            return result if isinstance(result, PromptBoundaryCheck) else None
        return None

    def _save_packet_if_requested(
        self,
        packet: PromptPacket,
        request: PromptCompileRequest,
    ) -> PromptPacket:
        if not request.store_packet:
            return packet
        if self._settings is not None and not bool(
            getattr(self._settings, "prompt_store_packets", True)
        ):
            return packet
        save = getattr(self._repository, "save_packet", None)
        result = save(packet) if callable(save) else packet
        return result if isinstance(result, PromptPacket) else packet

    def _create_manifest(
        self,
        packet: PromptPacket,
        boundary_check: PromptBoundaryCheck | None,
    ) -> ModelInputManifest | None:
        create = getattr(self._manifest_service, "create_from_packet", None)
        if not callable(create):
            return None
        try:
            result = create(packet, boundary_check)
            return result if isinstance(result, ModelInputManifest) else None
        except PermissionError:
            raise
        except Exception:
            return None


def _packet_status(boundary_check: PromptBoundaryCheck | None) -> PromptPacketStatus:
    if boundary_check is None:
        return "compiled"
    if not boundary_check.safe or boundary_check.status == "blocked":
        return "blocked"
    if boundary_check.status == "warning" or boundary_check.warnings:
        return "warning"
    return "compiled"


def _estimate_tokens(char_count: int) -> int:
    return max(1, (char_count + 3) // 4) if char_count else 0


def _section_manifest(section: PromptSection) -> dict[str, Any]:
    return {
        "section_id": section.section_id,
        "section_type": section.section_type,
        "title": section.title,
        "content_hash": hash_prompt_sections([section]),
        "priority": section.priority,
        "source_type": section.source_type,
        "source_id": section.source_id,
        "trust_level": section.trust_level,
        "required": section.required,
        "redacted": section.redacted,
    }


def _preview(sections: list[PromptSection]) -> str:
    return "\n\n".join(f"## {section.title}\n{section.content}" for section in sections)


def _input_refs(request: PromptCompileRequest) -> list[str]:
    return [
        ref
        for ref in [
            request.context_packet_id,
            request.dialogue_session_id,
            request.response_id,
            request.explanation_id,
            request.instruction_resolution_id,
            request.grounding_verification_id,
        ]
        if ref
    ]


def _scope_matches(owner_scope: list[str], scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(scope))


__all__ = ["PromptPacketCompiler"]
