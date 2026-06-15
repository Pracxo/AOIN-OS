"""LiteLLM-compatible HTTP model gateway adapter boundary."""

from datetime import UTC, datetime
from time import perf_counter

import httpx

from aion_brain.contracts.reasoning import ModelCallRecord, ModelRouteDecision, PromptPacket


class LiteLLMHTTPAdapter:
    """Optional LiteLLM-compatible HTTP adapter without importing LiteLLM."""

    def __init__(
        self,
        *,
        base_url: str = "http://litellm:4000",
        timeout_seconds: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    def complete(self, prompt: PromptPacket, route: ModelRouteDecision) -> ModelCallRecord:
        """Complete a prompt through a LiteLLM-compatible HTTP endpoint."""
        started = perf_counter()
        try:
            with httpx.Client(
                timeout=self._timeout_seconds,
                transport=self._transport,
            ) as client:
                response = client.post(
                    f"{self._base_url}/v1/chat/completions",
                    json=_chat_completion_body(prompt, route),
                )
                response.raise_for_status()
                payload = response.json()
        except Exception:
            return _failed_record(prompt, route, "litellm_http_request_failed")
        latency_ms = int((perf_counter() - started) * 1000)
        content = _extract_content(payload)
        return ModelCallRecord(
            model_call_id=f"model-call-{prompt.prompt_id}",
            trace_id=prompt.trace_id,
            reasoning_id=route.reasoning_id,
            provider=route.selected_provider,
            model=route.selected_model,
            mode=route.mode,
            request={"prompt_id": prompt.prompt_id, "route_id": route.route_id},
            response={
                "summary": content,
                "interpretation": content,
                "suggested_next_actions": [],
                "requires_clarification": False,
                "clarification_questions": [],
                "confidence": 0.7,
            },
            status="completed",
            latency_ms=latency_ms,
            cost_estimate=0.0,
            created_at=datetime.now(UTC),
        )


class LiteLLMAdapter:
    """Legacy placeholder kept for compatibility with earlier v0.1 tests.

    LiteLLM is planned as AION's optional model gateway adapter.
    AION contracts must remain independent of LiteLLM internals.
    """

    def complete(self, prompt: PromptPacket, route: ModelRouteDecision) -> ModelCallRecord:
        """Complete through a future direct LiteLLM boundary."""
        raise NotImplementedError("Direct LiteLLM package integration is not implemented.")


def _chat_completion_body(prompt: PromptPacket, route: ModelRouteDecision) -> dict[str, object]:
    return {
        "model": route.selected_model,
        "messages": [
            {"role": "system", "content": "\n".join(prompt.system_instructions)},
            {"role": "user", "content": prompt.goal},
        ],
        "max_tokens": prompt.token_budget_hint,
    }


def _extract_content(payload: object) -> str:
    if not isinstance(payload, dict):
        return ""
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0]
    if not isinstance(first, dict):
        return ""
    message = first.get("message")
    if isinstance(message, dict):
        return str(message.get("content", ""))
    return str(first.get("text", ""))


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
