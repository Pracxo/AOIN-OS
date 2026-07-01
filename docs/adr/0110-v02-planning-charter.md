# ADR 0110: v0.2 Planning Charter

## Status

Accepted

## Context

AION-118 created the post-v0.1 release candidate gate and froze the evidence
baseline before v0.2 planning. AION now needs a structured planning framework
before any runtime implementation can be proposed.

## Decision

Decision: add v0.2 planning charter.

Decision: AION-119 does not approve implementation.

Decision: no v0.2 release or tag is created.

Decision: future v0.2 implementation requires explicit ADRs and gate evidence.

## Reason

Reason: AION needs structured planning before runtime implementation.

## Consequence

Consequence: v0.2 work is limited to gated planning until explicit approval.

## Constraints

Constraint: no runtime enablement.

Constraint: no external calls.

Constraint: no credentials/tokens.

Constraint: no sandbox execution.

Constraint: no privileged bypass.

## Implementation Boundary

AION-119 adds planning docs, synthetic examples, static read-only console data,
tests, and repository-local checks only. It does not add API routers, SDK
resources, CLI command implementations, migrations, runtime config defaults,
package manager files, or domain module logic.
