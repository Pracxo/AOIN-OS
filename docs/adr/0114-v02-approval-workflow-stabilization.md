# ADR 0114: v0.2 Approval Workflow Stabilization

## Status

Accepted

## Context

AION-122 created the v0.2 implementation kickoff boundary, but future
implementation work still needs a stabilized approval workflow before requests
can be accepted, reviewed, rejected, expired, revoked, or escalated.

## Decision

Decision: add v0.2 approval workflow stabilization gate.

Decision: AION-123 does not approve implementation.

Decision: approval workflow stabilization does not enable runtime.

Decision: future implementation still requires explicit approval records, ADRs,
and gate evidence.

Decision: no v0.2 release or tag is created.

## Reason

Reason: AION needs a stable approval workflow before implementation work can be
requested.

## Consequences

Consequence: future runtime work must pass intake, decision, expiry,
revocation, and no-go checks.

Consequence: expired or revoked approvals return to not approved.

Consequence: dual-control can be required for high-risk workstreams without
creating an execution or release bypass.

## Constraints

Constraint: no runtime enablement.

Constraint: no external calls.

Constraint: no credentials/tokens.

Constraint: no sandbox execution.

Constraint: no privileged bypass.
