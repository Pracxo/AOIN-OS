"""LiteLLM-compatible HTTP adapter tests."""

import json
import sys

import httpx

from aion_brain.reasoning.litellm_adapter import LiteLLMHTTPAdapter
from tests.model_gateway_fakes import prompt
from tests.test_deterministic_reasoning_adapter import make_route


def test_litellm_http_adapter_uses_mocked_transport() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "mocked completion"}}]},
        )

    adapter = LiteLLMHTTPAdapter(
        base_url="http://litellm.test",
        transport=httpx.MockTransport(handler),
    )
    record = adapter.complete(prompt(), make_route())
    assert record.status == "completed"
    assert record.response["summary"] == "mocked completion"
    assert json.loads("{}") == {}


def test_litellm_http_adapter_does_not_import_litellm_package() -> None:
    assert "litellm" not in sys.modules
