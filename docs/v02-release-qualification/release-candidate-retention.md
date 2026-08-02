# AION-243 Candidate Retention Boundary

AION-243 must use a secure candidate root outside the repository with directory
mode `0700`.

Retention rules:

- retain exactly one candidate bundle
- retain exactly one local candidate image
- commit only redacted fingerprints and metadata
- retain no private qualification key
- retain the qualification public key and detached signatures
- remove temporary build directories
- remove comparison images and intermediate containers
- preserve the final candidate bundle until AION-244
- fail when the retained candidate is missing or altered
