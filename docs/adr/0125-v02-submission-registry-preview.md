# ADR 0125: v0.2 Submission Registry Preview

## Status

Accepted

## Context

AION-131 created the implementation request pack, AION-132 stabilized it, and
AION-133 completed request pack final review and the pre-approval submission
gate. AION now needs a submission registry boundary before implementation
candidates can enter approval review.

## Decision

Decision: add v0.2 submission registry preview.

Decision: AION-134 does not approve implementation.

Decision: submission registry and pre-approval queue remain preview-only.

Decision: submission approval and pre-approval queue item approval remain false.

Decision: no v0.2 release or tag is created.

## Reason

AION needs a submission registry boundary before implementation candidates can
enter approval review.

## Consequence

Future implementation candidates must remain unapproved until explicit approval
records, ADRs, and gate evidence exist.

## Constraints

Constraint: no runtime enablement.

Constraint: no external calls.

Constraint: no credentials/tokens.

Constraint: no sandbox execution.

Constraint: no privileged bypass.
