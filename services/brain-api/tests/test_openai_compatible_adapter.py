"""OpenAI-compatible HTTP adapter boundary tests."""

import sys

import httpx

from aion_brain.reasoning.openai_compatible_adapter import OpenAICompatibleHTTPAdapter
from tests.model_gateway_fakes import prompt
from tests.test_deterministic_reasoning_adapter import make_route


def test_openai_compatible_adapter_returns_auth_missing_when_unconfigured() -> None:
    adapter = OpenAICompatibleHTTPAdapter(base_url="http://provider.test", auth_token=None)
    record = adapter.complete(prompt(), make_route())
    assert record.status == "failed"
    assert record.response["reason"] == "provider_auth_not_configured"


def test_openai_compatible_adapter_uses_mocked_transport() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    adapter = OpenAICompatibleHTTPAdapter(
        base_url="http://provider.test",
        auth_token="test-token",
        transport=httpx.MockTransport(handler),
    )
    record = adapter.complete(prompt(), make_route())
    assert record.status == "completed"
    assert record.response["summary"] == "ok"


def test_openai_compatible_adapter_does_not_import_provider_sdks() -> None:
    assert "openai" not in sys.modules
    assert "anthropic" not in sys.modules
    assert "google.generativeai" not in sys.modules
