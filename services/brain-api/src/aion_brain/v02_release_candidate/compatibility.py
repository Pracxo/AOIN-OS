"""AION-243 release-candidate compatibility contracts."""

from aion_brain.contracts.v02_release_candidate import (
    V02CandidateCompatibilityMatrix,
    V02CandidateCompatibilityRecord,
    V02CandidateMigrationManifest,
    V02CandidateMigrationRecord,
)

__all__ = [
    "V02CandidateCompatibilityMatrix",
    "V02CandidateCompatibilityRecord",
    "V02CandidateMigrationManifest",
    "V02CandidateMigrationRecord",
]
