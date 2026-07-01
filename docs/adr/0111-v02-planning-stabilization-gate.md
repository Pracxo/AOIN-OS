# ADR 0111: v0.2 Planning Stabilization Gate

## Status

Accepted

## Context

AION-119 created the v0.2 planning charter and mapped future implementation
workstreams to ADR and gate dependencies. AION now needs stable v0.2 planning
governance before implementation work can be proposed.

## Decision

Decision: add v0.2 planning stabilization gate.

Decision: v0.2 remains planning-only after AION-120.

Decision: implementation approval remains false.

Decision: no v0.2 release or tag is created.

Decision: future implementation requires explicit ADRs, gate evidence, and
planning review.

## Reason

Reason: AION needs stable v0.2 planning governance before implementation work.

## Consequence

Consequence: v0.2 work remains constrained to approved planning backlog items.

## Constraints

Constraint: no runtime enablement.

Constraint: no external calls.

Constraint: no credentials/tokens.

Constraint: no sandbox execution.

Constraint: no privileged bypass.

## Implementation Boundary

AION-120 adds planning docs, synthetic examples, static read-only console data,
tests, and repository-local checks only. It does not add API routers, SDK
resources, CLI command implementations, migrations, runtime config defaults,
package manager files, runtime implementation, or domain module logic.
