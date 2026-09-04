"""Response projection for AION-248."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.live_provider_pilot import (
    SELECTED_MODEL_ID,
    LiveProviderResponseProjection,
    LiveProviderTransportResult,
    estimate_tokens_from_bytes,
)


def project_response(
    *,
    response_projection_id: str,
    request_projection_fingerprint: str,
    transport_result: LiveProviderTransportResult,
    created_at: datetime,
) -> LiveProviderResponseProjection:
    """Retain only the safe response projection."""

    if transport_result.provider_response_model_id != SELECTED_MODEL_ID:
        raise ValueError("provider response model mismatch")
    return LiveProviderResponseProjection(
        response_projection_id=response_projection_id,
        request_projection_fingerprint=request_projection_fingerprint,
        transport_result_fingerprint=transport_result.transport_result_fingerprint or "",
        provider_response_model_id=transport_result.provider_response_model_id,
        response_fingerprint=transport_result.response_fingerprint,
        response_byte_count=transport_result.response_byte_count,
        estimated_output_tokens=estimate_tokens_from_bytes(transport_result.response_byte_count),
        created_at=created_at,
    )
