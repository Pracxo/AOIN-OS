from __future__ import annotations

from types import SimpleNamespace

from aion_brain.contracts.responses import ResponseComposeRequest
from aion_brain.dialogue.repository import DialogueRepository
from aion_brain.responses.composer import ResponseComposer
from tests.dialogue_helpers import AllowPolicy


class FakePromptCompiler:
    def __init__(self) -> None:
        self.requests: list[object] = []

    def compile(self, request: object) -> object:
        self.requests.append(request)
        packet = SimpleNamespace(
            prompt_packet_id="prompt-packet-1",
            boundary_check_id="boundary-1",
            status="compiled",
        )
        manifest = SimpleNamespace(model_input_manifest_id="manifest-1")
        return SimpleNamespace(
            blocked=False,
            prompt_packet=packet,
            model_input_manifest=manifest,
        )


def test_response_composer_records_prompt_metadata() -> None:
    prompt_compiler = FakePromptCompiler()
    composer = ResponseComposer(
        DialogueRepository(),
        AllowPolicy(),
        prompt_compiler=prompt_compiler,
    )

    draft = composer.compose(
        ResponseComposeRequest(
            trace_id="trace-1",
            context={"goal": "answer", "owner_scope": ["workspace:main"]},
            reasoning_result={"summary": "ok"},
            plan={},
            metadata={},
        )
    )

    assert prompt_compiler.requests
    assert draft.metadata["prompt_packet_id"] == "prompt-packet-1"
    assert draft.metadata["model_input_manifest_id"] == "manifest-1"
