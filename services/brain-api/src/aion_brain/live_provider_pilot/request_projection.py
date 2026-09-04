"""Request projection and payload validation for AION-248."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.live_provider_pilot import (
    LiveProviderEndpointPolicy,
    LiveProviderRequestPolicy,
    LiveProviderRequestProjection,
    LiveProviderScenarioCode,
    content_fingerprint,
    estimate_tokens_from_bytes,
    live_provider_fingerprint,
    validate_responses_payload,
)
from aion_brain.production_auth.canonical import canonical_json_bytes


def project_request(
    *,
    request_id: str,
    scenario_code: LiveProviderScenarioCode,
    prompt_text: str,
    payload: dict[str, object],
    maximum_output_tokens: int,
    endpoint_policy: LiveProviderEndpointPolicy,
    created_at: datetime,
) -> LiveProviderRequestProjection:
    """Validate and retain only the request projection."""

    validate_responses_payload(payload)
    payload_bytes = canonical_json_bytes(payload)
    request_policy = LiveProviderRequestPolicy()
    return LiveProviderRequestProjection(
        request_id=request_id,
        scenario_code=scenario_code,
        endpoint_policy_fingerprint=endpoint_policy.endpoint_policy_fingerprint or "",
        request_policy_fingerprint=live_provider_fingerprint(
            request_policy.model_dump(mode="json")
        ),
        request_fingerprint=content_fingerprint("live_provider_request", payload_bytes),
        request_byte_count=len(payload_bytes),
        estimated_input_tokens=estimate_tokens_from_bytes(len(prompt_text.encode("utf-8"))),
        maximum_output_tokens=maximum_output_tokens,
        created_at=created_at,
    )


def reject_context_budget_overflow() -> None:
    """Context budget overflow is rejected before credential access."""

    raise ValueError("context budget overflow rejected")


def reject_output_budget_overflow() -> None:
    """Output budget overflow is rejected before credential access."""

    raise ValueError("output budget overflow rejected")
