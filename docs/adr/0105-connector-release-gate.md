# ADR 0105: Connector Release Gate

## Status

Accepted.

## Context

AION-106 through AION-113 introduced connector design, disabled runtime proof,
runtime review, dry-run simulation, policy catalog, sandbox design, and
credential architecture. These artifacts need one release gate before any later
runtime connector implementation can be considered.

## Decision

Add a connector release gate and safety freeze.

Connector runtime remains disabled after AION-114.

Connector implementation is not approved by this release gate.

Future connector implementation requires a new explicit ADR and must pass
release gate evidence.

## Reason

AION needs a consolidated connector safety gate before future runtime work.

## Consequences

Connector work can proceed only as gated future implementation. Release
evidence can prove readiness for future review, but it cannot enable runtime
behavior or approve implementation.

## Constraints

- no runtime enablement
- no external calls
- no credentials or tokens
- no sandbox execution
- no privileged bypass
