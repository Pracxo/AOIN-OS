"""Prompt compiler integration for provider egress preview metadata."""

from __future__ import annotations

from aion_brain.contracts.prompts import PromptPacket, PromptSection
from aion_brain.prompts.compiler import PromptPacketCompiler


def test_prompt_compiler_builds_redacted_egress_preview_metadata() -> None:
    compiler = PromptPacketCompiler(repository=object(), policy_adapter=None)
    packet = PromptPacket(
        prompt_packet_id="prompt-packet-1",
        status="compiled",
        packet_type="generic",
        owner_scope=["workspace:main"],
        sections=[
            PromptSection(
                section_id="section-1",
                section_type="retrieved_context",
                title="Context",
                content="Generic context.",
                priority=10,
                trust_level="system",
                required=True,
                redacted=False,
            )
        ],
        rendered_hash="hash-1",
        token_estimate=10,
        char_count=16,
    )

    metadata = compiler.build_egress_preview_metadata(packet)

    assert metadata["prompt_packet_ref"] == "prompt-packet-1"
    assert metadata["raw_prompt_included"] is False
    assert metadata["hidden_reasoning_included"] is False
