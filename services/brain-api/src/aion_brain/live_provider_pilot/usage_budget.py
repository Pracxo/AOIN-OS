"""Usage-budget records for AION-248."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.live_provider_pilot import (
    MAXIMUM_TOTAL_INPUT_TOKENS,
    MAXIMUM_TOTAL_OUTPUT_TOKENS,
    LiveProviderRequestProjection,
    LiveProviderResponseProjection,
    LiveProviderTransportResult,
    LiveProviderUsageRecord,
)


def create_usage_record(
    *,
    usage_id: str,
    request: LiveProviderRequestProjection,
    response: LiveProviderResponseProjection,
    transport_result: LiveProviderTransportResult,
    created_at: datetime,
) -> LiveProviderUsageRecord:
    """Create a bounded usage record."""

    if transport_result.input_tokens > MAXIMUM_TOTAL_INPUT_TOKENS:
        raise ValueError("input token budget exceeded")
    if transport_result.output_tokens > MAXIMUM_TOTAL_OUTPUT_TOKENS:
        raise ValueError("output token budget exceeded")
    return LiveProviderUsageRecord(
        usage_id=usage_id,
        request_projection_fingerprint=request.projection_fingerprint or "",
        response_projection_fingerprint=response.projection_fingerprint or "",
        input_tokens=transport_result.input_tokens,
        output_tokens=transport_result.output_tokens,
        total_tokens=transport_result.total_tokens,
        reasoning_tokens=transport_result.reasoning_tokens,
        cached_tokens=transport_result.cached_tokens,
        request_byte_count=request.request_byte_count,
        response_byte_count=response.response_byte_count,
        latency_ms=transport_result.latency_ms,
        http_status=transport_result.http_status,
        provider_status=transport_result.provider_status,
        created_at=created_at,
    )
