# 0207: Deterministic Local v0.2 Release-Candidate Artifact Bundle Build and Retention

## Status

Accepted.

## Context

AION-242 authorized exactly one deterministic local v0.2 release-candidate
artifact build under `AION-242-V02RQ-0003`. The authorization permits local
source, package, OCI image, SBOM, provenance, checksum, qualification-signature,
compatibility, migration and draft release-note evidence. It does not authorize
publication, tagging, registry use, package-index upload or production
deployment.

## Decision

AION-243 adds a pure release-candidate contract package and one uninstalled
runner. The package defines strict immutable evidence contracts and performs no
Docker, filesystem or subprocess work. The runner builds from a clean immutable
candidate source commit, uses the pinned offline Hatchling toolchain, invokes
Docker with `--pull=false` and `--network=none`, creates one local candidate
bundle and retains one local candidate image.

The candidate identifier is `aion-v0.2.0-rc.1` and the Python package version is
`0.2.0rc1`.

## Consequences

The retained candidate is evidence for AION-244. AION-244 remains responsible
for independent evaluation and any explicit v0.2 tag or release authorization.
Until that decision, `v02_release_ready=false`, no v0.2 tag exists, no GitHub
release exists, and the candidate remains unpublished and undeployed.
