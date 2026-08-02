"""AION-243 release-candidate authorization contracts."""

from aion_brain.contracts.v02_release_candidate import (
    V02ReleaseCandidateAuthorizationEnvelope,
    canonical_authorization_envelope,
)

__all__ = ["V02ReleaseCandidateAuthorizationEnvelope", "canonical_authorization_envelope"]
