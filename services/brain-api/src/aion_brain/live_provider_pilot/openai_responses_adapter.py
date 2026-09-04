"""OpenAI Responses API payload construction and response parsing."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from aion_brain.contracts.live_provider_pilot import (
    REASONING_EFFORT,
    SELECTED_MODEL_ID,
    validate_responses_payload,
)


def build_responses_payload(
    *,
    prompt: str,
    maximum_output_tokens: int,
    model_id: str = SELECTED_MODEL_ID,
) -> dict[str, object]:
    """Build the exact Responses API payload without performing transport."""

    payload: dict[str, object] = {
        "model": model_id,
        "input": prompt,
        "store": False,
        "background": False,
        "stream": False,
        "max_output_tokens": maximum_output_tokens,
        "reasoning": {"effort": REASONING_EFFORT},
    }
    validate_responses_payload(payload)
    return payload


def extract_text_from_response(payload: Mapping[str, Any]) -> str:
    """Extract text from common Responses API response shapes."""

    direct = payload.get("output_text")
    if isinstance(direct, str) and direct:
        return direct
    output = payload.get("output")
    if isinstance(output, Sequence) and not isinstance(output, str | bytes | bytearray):
        parts: list[str] = []
        for item in output:
            if not isinstance(item, Mapping):
                continue
            content = item.get("content")
            if isinstance(content, Sequence) and not isinstance(content, str | bytes | bytearray):
                for content_item in content:
                    if isinstance(content_item, Mapping):
                        text = content_item.get("text")
                        if isinstance(text, str) and text:
                            parts.append(text)
        if parts:
            return "\n".join(parts)
    raise ValueError("provider response did not contain completed text output")


def extract_usage(payload: Mapping[str, Any]) -> dict[str, int]:
    """Extract token counters with absent values treated as zero."""

    usage = payload.get("usage")
    if not isinstance(usage, Mapping):
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "reasoning_tokens": 0,
            "cached_tokens": 0,
        }
    input_tokens = _non_negative_int(usage.get("input_tokens"))
    output_tokens = _non_negative_int(usage.get("output_tokens"))
    total_tokens = _non_negative_int(usage.get("total_tokens")) or input_tokens + output_tokens
    output_details = usage.get("output_tokens_details")
    input_details = usage.get("input_tokens_details")
    reasoning_tokens = 0
    cached_tokens = 0
    if isinstance(output_details, Mapping):
        reasoning_tokens = _non_negative_int(output_details.get("reasoning_tokens"))
    if isinstance(input_details, Mapping):
        cached_tokens = _non_negative_int(input_details.get("cached_tokens"))
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "reasoning_tokens": reasoning_tokens,
        "cached_tokens": cached_tokens,
    }


def _non_negative_int(value: object) -> int:
    if isinstance(value, int) and value >= 0:
        return value
    return 0
