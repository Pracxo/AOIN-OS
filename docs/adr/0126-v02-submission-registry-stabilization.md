# 0126: v0.2 Submission Registry Stabilization

## Status

Accepted

## Context

AION-134 created the v0.2 submission registry preview and pre-approval queue
boundary. AION now needs a stable pre-approval submission baseline before
implementation approval can be considered.

## Decision

Decision: add v0.2 submission registry stabilization gate.

Decision: AION-135 does not approve implementation.

Decision: submission registry and pre-approval queue remain preview-only.

Decision: submission approval and pre-approval queue item approval remain false.

Decision: future implementation still requires explicit approval records, ADRs,
and gate evidence.

Decision: no v0.2 release or tag is created.

## Reason

AION needs a stable pre-approval submission baseline before implementation
approval can be considered.

## Consequence

Future implementation candidates remain blocked until explicit approval records
are created.

## Constraints

Constraint: no runtime enablement.

Constraint: no external calls.

Constraint: no credentials/tokens.

Constraint: no sandbox execution.

Constraint: no privileged bypass.
