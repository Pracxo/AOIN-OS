"""Generic OpenAI-compatible HTTP model gateway adapter."""

from datetime import UTC, datetime
from time import perf_counter

import httpx

from aion_brain.contracts.reasoning import ModelCallRecord, ModelRouteDecision, PromptPacket
from aion_brain.reasoning.litellm_adapter import _chat_completion_body, _extract_content


class OpenAICompatibleHTTPAdapter:
    """Optional HTTP adapter for OpenAI-compatible APIs without provider SDKs."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        auth_token: str | None = None,
        timeout_seconds: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._base_url = (base_url or "").rstrip("/")
        self._auth_token = auth_token
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    def complete(self, prompt: PromptPacket, route: ModelRouteDecision) -> ModelCallRecord:
        """Complete through a generic OpenAI-compatible HTTP endpoint."""
        if not self._base_url:
            return _failed_record(prompt, route, "provider_endpoint_not_configured")
        if not self._auth_token:
            return _failed_record(prompt, route, "provider_auth_not_configured")
        started = perf_counter()
        try:
            with httpx.Client(
                timeout=self._timeout_seconds,
                transport=self._transport,
            ) as client:
                response = client.post(
                    f"{self._base_url}/v1/chat/completions",
                    headers={"Authorization": "Bearer [REDACTED]"},
                    json=_chat_completion_body(prompt, route),
                )
                response.raise_for_status()
                payload = response.json()
        except Exception:
            return _failed_record(prompt, route, "openai_compatible_http_request_failed")
        return ModelCallRecord(
            model_call_id=f"model-call-{prompt.prompt_id}",
            trace_id=prompt.trace_id,
            reasoning_id=route.reasoning_id,
            provider=route.selected_provider,
            model=route.selected_model,
            mode=route.mode,
            request={"prompt_id": prompt.prompt_id, "route_id": route.route_id},
            response={
                "summary": _extract_content(payload),
                "interpretation": _extract_content(payload),
                "suggested_next_actions": [],
                "requires_clarification": False,
                "clarification_questions": [],
                "confidence": 0.7,
            },
            status="completed",
            latency_ms=int((perf_counter() - started) * 1000),
            cost_estimate=0.0,
            created_at=datetime.now(UTC),
        )


def _failed_record(prompt: PromptPacket, route: ModelRouteDecision, reason: str) -> ModelCallRecord:
    return ModelCallRecord(
        model_call_id=f"model-call-{prompt.prompt_id}",
        trace_id=prompt.trace_id,
        reasoning_id=route.reasoning_id,
        provider=route.selected_provider,
        model=route.selected_model,
        mode=route.mode,
        request={"prompt_id": prompt.prompt_id, "route_id": route.route_id},
        response={"reason": reason},
        status="failed",
        latency_ms=None,
        cost_estimate=0.0,
        created_at=datetime.now(UTC),
    )
