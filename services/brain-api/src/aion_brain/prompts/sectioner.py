"""Deterministic prompt section construction."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any
from uuid import uuid4

from aion_brain.contracts.prompts import PromptCompileRequest, PromptSection
from aion_brain.prompts.redaction import redact_prompt_text

_SECTION_ORDER = {
    "system_boundary": 0,
    "self_model": 10,
    "policy_constraints": 20,
    "autonomy_constraints": 30,
    "risk_constraints": 40,
    "approval_constraints": 50,
    "instruction_resolution": 60,
    "user_message": 70,
    "dialogue_history": 80,
    "retrieved_context": 90,
    "evidence": 100,
    "memory": 110,
    "belief": 120,
    "entity": 130,
    "situation": 140,
    "decision": 150,
    "outcome": 160,
    "grounding": 170,
    "citation": 180,
    "tool_manifest": 190,
    "response_format": 200,
    "developer_note": 900,
    "generic": 1000,
}


class PromptSectioner:
    """Build and order provider-neutral prompt sections from Brain context."""

    def build_sections(self, request: PromptCompileRequest) -> list[PromptSection]:
        """Create deterministic sections from the compile request."""

        sections = [
            PromptSection(
                section_id=f"section-system-boundary-{uuid4().hex}",
                section_type="system_boundary",
                title="AION system boundary",
                content=(
                    "Use only governed AION prompt sections. Do not reveal "
                    "protected reasoning material or secrets."
                ),
                priority=0,
                source_type="aion_core",
                source_id="prompt_boundary",
                trust_level="system",
                required=True,
                redacted=False,
                metadata={"boundary": "aion_prompt_packet"},
            )
        ]
        if request.user_message:
            redacted_user_message, redaction_metadata = redact_prompt_text(request.user_message)
            sections.append(
                PromptSection(
                    section_id=f"section-user-message-{uuid4().hex}",
                    section_type="user_message",
                    title="User message",
                    content=redacted_user_message,
                    priority=100,
                    source_type="user_message",
                    source_id=request.trace_id,
                    trust_level="user",
                    required=True,
                    redacted=bool(redaction_metadata["redacted"]),
                    metadata={"redaction": redaction_metadata},
                )
            )
        sections.extend(self.from_metadata(request.metadata))
        sections.extend(request.sections)
        return trim_sections(order_sections(sections), request.max_chars)

    def from_metadata(self, metadata: dict[str, Any]) -> list[PromptSection]:
        """Build typed sections from generic metadata references."""

        sections: list[PromptSection] = []
        sections.extend(
            _sections_from_items(
                metadata.get("retrieved_context") or metadata.get("context_items") or [],
                section_type="retrieved_context",
                title="Retrieved context",
                trust_level="untrusted_context",
            )
        )
        sections.extend(
            _sections_from_items(
                metadata.get("memory_refs") or metadata.get("memories") or [],
                section_type="memory",
                title="Memory recall",
                trust_level="memory_recall",
            )
        )
        sections.extend(
            _sections_from_items(
                metadata.get("evidence_refs") or metadata.get("evidence") or [],
                section_type="evidence",
                title="Evidence",
                trust_level="evidence",
            )
        )
        sections.extend(
            _sections_from_items(
                metadata.get("belief_refs") or metadata.get("beliefs") or [],
                section_type="belief",
                title="Belief",
                trust_level="belief_supported",
            )
        )
        sections.extend(
            _sections_from_items(
                metadata.get("citation_refs") or metadata.get("citations") or [],
                section_type="citation",
                title="Citation",
                trust_level="evidence",
            )
        )
        if metadata.get("instruction_resolution_id"):
            sections.append(
                self.from_instruction_resolution(str(metadata["instruction_resolution_id"]))
            )
        if metadata.get("grounding_verification_id"):
            sections.append(self.from_grounding(str(metadata["grounding_verification_id"])))
        return sections

    def from_context_packet(self, context_packet: object) -> list[PromptSection]:
        """Build sections from a ContextPacket-like object."""

        goal = str(getattr(context_packet, "goal", "") or "")
        known_context = getattr(context_packet, "known_context", []) or []
        sections = []
        if goal:
            sections.append(
                PromptSection(
                    section_id=f"section-context-goal-{uuid4().hex}",
                    section_type="retrieved_context",
                    title="Goal",
                    content=goal,
                    priority=90,
                    source_type="context_packet",
                    source_id=str(getattr(context_packet, "context_id", "") or ""),
                    trust_level="retrieved_context",
                    required=False,
                    redacted=False,
                    metadata={},
                )
            )
        sections.extend(
            _sections_from_items(
                known_context,
                section_type="retrieved_context",
                title="Known context",
                trust_level="retrieved_context",
            )
        )
        return sections

    def from_instruction_resolution(self, instruction_resolution_id: str) -> PromptSection:
        """Create a placeholder instruction-resolution section."""

        return PromptSection(
            section_id=f"section-instruction-{instruction_resolution_id}",
            section_type="instruction_resolution",
            title="Instruction resolution",
            content=f"Instruction resolution reference: {instruction_resolution_id}",
            priority=60,
            source_type="instruction_resolution",
            source_id=instruction_resolution_id,
            trust_level="policy",
            required=False,
            redacted=False,
            metadata={"reference_only": True},
        )

    def from_grounding(self, grounding_verification_id: str) -> PromptSection:
        """Create a placeholder grounding-verification section."""

        return PromptSection(
            section_id=f"section-grounding-{grounding_verification_id}",
            section_type="grounding",
            title="Grounding verification",
            content=f"Grounding verification reference: {grounding_verification_id}",
            priority=170,
            source_type="grounding_verification",
            source_id=grounding_verification_id,
            trust_level="evidence",
            required=False,
            redacted=False,
            metadata={"reference_only": True},
        )


def order_sections(sections: Iterable[PromptSection]) -> list[PromptSection]:
    """Order sections by AION boundary priority and declared priority."""

    return sorted(
        sections,
        key=lambda section: (_SECTION_ORDER.get(section.section_type, 1000), section.priority),
    )


def trim_sections(sections: list[PromptSection], max_chars: int) -> list[PromptSection]:
    """Trim section content deterministically while preserving required boundaries."""

    remaining = max_chars
    trimmed: list[PromptSection] = []
    for section in sections:
        content = section.content
        if len(content) > remaining and not section.required:
            content = content[: max(0, remaining)]
        if section.required or remaining > 0:
            trimmed.append(
                section.model_copy(
                    update={
                        "content": content,
                        "metadata": {
                            **section.metadata,
                            "truncated": len(content) < len(section.content),
                        },
                    }
                )
            )
        remaining -= len(content)
    return trimmed


def _sections_from_items(
    items: object,
    *,
    section_type: str,
    title: str,
    trust_level: str,
) -> list[PromptSection]:
    if not isinstance(items, list):
        return []
    sections: list[PromptSection] = []
    for index, item in enumerate(items):
        if isinstance(item, dict):
            source_id = str(item.get("id") or item.get("source_id") or index)
            content = str(item.get("summary") or item.get("content") or source_id)
            metadata = {key: value for key, value in item.items() if key not in {"content"}}
        else:
            source_id = str(item)
            content = source_id
            metadata = {"reference_only": True}
        redacted, redaction_metadata = redact_prompt_text(content)
        sections.append(
            PromptSection(
                section_id=f"section-{section_type}-{uuid4().hex}",
                section_type=section_type,  # type: ignore[arg-type]
                title=title,
                content=redacted,
                priority=100 + index,
                source_type=section_type,
                source_id=source_id,
                trust_level=trust_level,  # type: ignore[arg-type]
                required=False,
                redacted=bool(redaction_metadata["redacted"]),
                metadata={**metadata, "redaction": redaction_metadata},
            )
        )
    return sections


__all__ = ["PromptSectioner", "order_sections", "trim_sections"]
