"""Trust and uncertainty helpers for AION-248."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.live_provider_pilot import (
    LiveProviderResponseProjection,
    LiveProviderTrustAssessment,
    LiveProviderTrustClass,
    LiveProviderUncertaintyProjection,
)


def assess_live_response_trust(
    *,
    trust_id: str,
    response: LiveProviderResponseProjection,
    schema_validated: bool,
    created_at: datetime,
) -> LiveProviderTrustAssessment:
    """Classify live output as untrusted even after local validation."""

    trust_class = (
        LiveProviderTrustClass.schema_validated_untrusted_live_provider_output
        if schema_validated
        else LiveProviderTrustClass.untrusted_live_provider_output
    )
    return LiveProviderTrustAssessment(
        trust_id=trust_id,
        response_projection_fingerprint=response.projection_fingerprint or "",
        trust_class=trust_class,
        created_at=created_at,
    )


def project_live_uncertainty(
    *,
    uncertainty_id: str,
    response: LiveProviderResponseProjection,
    confidence_score: float,
    created_at: datetime,
) -> LiveProviderUncertaintyProjection:
    """Create a bounded uncertainty projection."""

    return LiveProviderUncertaintyProjection(
        uncertainty_id=uncertainty_id,
        response_projection_fingerprint=response.projection_fingerprint or "",
        confidence_score=confidence_score,
        created_at=created_at,
    )
