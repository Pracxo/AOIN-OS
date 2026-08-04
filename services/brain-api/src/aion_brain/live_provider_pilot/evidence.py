"""Evidence-bundle helpers for AION-248."""

from __future__ import annotations

from aion_brain.contracts.live_provider_pilot import (
    LiveProviderEvidenceBundle,
    assert_no_protected_material,
)


def create_evidence_bundle(**payload: object) -> LiveProviderEvidenceBundle:
    """Create and validate a redacted evidence bundle."""

    assert_no_protected_material(payload)
    return LiveProviderEvidenceBundle.model_validate(payload)
