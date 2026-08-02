# 0206: Controlled Staging Evaluation And Deterministic v0.2 Release-Candidate Artifact Build Authorization

## Status

Accepted.

## Context

AION-241 produced controlled isolated local staging evidence from immutable
source, two offline local builds, local-only staging artifacts, SBOM,
provenance, health, security, degradation, rollback and cleanup evidence. The
staging artifact is not a release candidate and was never published, tagged or
deployed to production.

## Decision

AION-242 accepts `AION-V02RQPE-002` as the operator evaluation for AION-241. All
28 hard-gated scenarios pass. `AION-240-V02RQ-0002` is closed, consumed by
AION-241, expired and non-reusable.

On this PASS, `AION-242-V02RQ-0003` becomes the sole active v0.2 Release
Qualification authorization for AION-243.

## Consequences

AION-243 may build exactly one deterministic, locally retained v0.2
release-candidate artifact bundle. That candidate may include the source
archive, Brain API OCI candidate image, SDK wheel and source distribution,
Operator Console bundle, SBOM, provenance, checksums, qualification signatures,
compatibility evidence, migration evidence and release notes draft.

AION-243 may not push, publish, tag, create a GitHub release or deploy to
production. AION-244 remains the final release-candidate evaluation and explicit
v0.2 tag/release authorization decision.
