# AION-243 Candidate Threat Model

AION-243 must guard against:

- source-snapshot substitution
- unauthorized runtime-source change
- package-version mismatch
- dependency drift
- base-image drift
- build-network escape
- registry interaction
- artifact substitution
- archive path traversal
- non-deterministic archive metadata
- OCI layer substitution
- SBOM omission
- provenance forgery
- checksum-manifest tampering
- signature substitution
- qualification-key persistence
- candidate-bundle deletion
- candidate-bundle path substitution
- compatibility evidence forgery
- migration evidence omission
- release-note mismatch
- Git tag creation
- GitHub release creation
- production deployment
- public publication before AION-244
