from __future__ import annotations

from tests.prompt_helpers import compile_request, compiler


def test_prompt_compiler_emits_visual_telemetry_events() -> None:
    prompt_compiler, _, _ = compiler()

    result = prompt_compiler.compile(compile_request())

    assert result.prompt_packet.prompt_packet_id
    telemetry = prompt_compiler._telemetry_service.events  # type: ignore[attr-defined]
    assert {event.event_type for event in telemetry} >= {
        "prompt_boundary_checked",
        "prompt_packet_compiled",
        "model_input_manifest_created",
    }
