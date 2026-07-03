# 0117: v0.2 Workstream Proposal Registry

## Status

Accepted

## Context

AION-125 froze the v0.2 pre-implementation master baseline. AION now needs a controlled registry for future workstream proposals before any implementation request can be reviewed or queued.

## Decision

Decision: add v0.2 workstream proposal registry.

Decision: AION-126 does not approve implementation.

Decision: proposal registry and approval queue remain preview-only.

Decision: future implementation still requires explicit approval records, ADRs, and gate evidence.

Decision: no v0.2 release or tag is created.

## Reason

Reason: AION needs a controlled proposal registry before any implementation workstream can be approved.

## Consequence

Consequence: future workstreams must enter through the registry and remain blocked until approval.

## Constraints

Constraint: no runtime enablement.

Constraint: no external calls.

Constraint: no credentials/tokens.

Constraint: no sandbox execution.

Constraint: no privileged bypass.
