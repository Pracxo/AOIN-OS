# 0071: Release Candidate Gate

## Status

Accepted.

## Decision

AION Brain includes a local Release Candidate Gate for v0.1. The gate produces
frontend-agnostic, SDK-accessible, CLI-accessible Brain-owned records:
release candidates, verification matrices, verification checks, gate runs,
findings, evidence packs, and reports.

## Reason

AION needs one final local readiness surface that aggregates existing quality,
kernel, policy, contract, operator, resource, bootstrap, golden path, freeze,
and release package evidence before a release candidate is considered ready.

## Constraints

- No deployment.
- No publishing.
- No automatic tagging.
- No source-code mutation.
- No external service calls.
- No enabling disabled runtime features.
- No domain-specific release behavior.
- Evidence packs and reports must be redacted.

## Consequences

Future release flows can consume a stable Brain-owned RC report without
coupling to local shell scripts, SQLAlchemy rows, Docker internals, OPA client
objects, SDK implementation details, or operator UI surfaces.
