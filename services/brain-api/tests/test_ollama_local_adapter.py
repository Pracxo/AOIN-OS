from __future__ import annotations

import pytest

from aion_brain.live_provider_pilot.ollama_local_adapter import build_chat_payload, project_response


def test_payload_is_exact_and_provider_neutral() -> None:
    payload = build_chat_payload(prompt="synthetic", model_digest="d", frozen_digest="d")
    assert payload["model"] == "gpt-oss:20b"
    assert payload["stream"] is False
    assert payload["think"] == "low"
    assert payload["options"] == {"num_ctx": 32768}
    assert "tools" not in payload


def test_digest_and_tool_calls_fail_closed() -> None:
    with pytest.raises(ValueError):
        build_chat_payload(prompt="x", model_digest="drift", frozen_digest="d")
    with pytest.raises(ValueError):
        project_response(
            {"model": "gpt-oss:20b", "message": {"content": "x", "tool_calls": [{"name": "x"}]}},
            model_digest="d",
            frozen_digest="d",
        )
