from __future__ import annotations

from aion_brain.contracts.prompts import PromptPreviewRequest
from aion_brain.prompts.preview import PromptPreviewService
from tests.prompt_helpers import AllowPolicy, compile_request, compiler


def test_prompt_preview_supports_hashes_only() -> None:
    prompt_compiler, _, _ = compiler()
    result = prompt_compiler.compile(compile_request())
    preview = PromptPreviewService(prompt_compiler, AllowPolicy()).preview(
        PromptPreviewRequest(
            prompt_packet_id=result.prompt_packet.prompt_packet_id,
            owner_scope=["workspace:main"],
            redaction_level="hashes_only",
        )
    )

    assert result.prompt_packet.rendered_hash in preview.preview
