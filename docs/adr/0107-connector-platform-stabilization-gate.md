# ADR 0107: Connector Platform Stabilization Gate

## Status

Accepted.

## Context

AION-106 through AION-115 established the connector boundary, disabled runtime
preview, runtime review gate, synthetic dry-run simulator, policy catalog,
sandbox design, credential architecture, release gate, safety freeze, and
platform checkpoint. AION now needs stable connector regression evidence before
implementation work can be proposed.

## Decision

Decision: add connector platform stabilization gate.

Decision: connector phase remains frozen after AION-116.

Decision: connector implementation remains unapproved.

Decision: future connector implementation requires a new ADR and must pass
connector platform stabilization.

## Reason

Reason: AION needs stable connector regression evidence before implementation
work.

## Consequence

Consequence: connector work can proceed only from a stable, gated baseline.

The stabilization gate provides a long-running regression matrix and phase
freeze gate, but it does not authorize connector runtime behavior.

## Constraints

Constraint: no runtime enablement.

Constraint: no external calls.

Constraint: no credentials/tokens.

Constraint: no sandbox execution.

Constraint: no privileged bypass.
