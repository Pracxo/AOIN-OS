# 0127: v0.2 Pre-Approval Review Board

## Status

Accepted

## Context

AION-134 created the submission registry preview and AION-135 stabilized the submission registry and pre-approval queue. AION needs a review routing boundary before implementation candidates can enter formal decision review.

## Decision

Decision: add v0.2 pre-approval review board.

Decision: AION-136 does not approve implementation.

Decision: review board routing remains planning-only.

Decision: review board decisions cannot enable runtime.

Decision: review board decision approval remains false.

Decision: no v0.2 release or tag is created.

## Consequences

Future candidates must pass routing, evidence, reviewer, ADR, and gate checks before approval can be considered.

Review board readiness remains separate from implementation approval, runtime enablement, submission approval, request pack approval, pre-approval queue approval, and release approval.

## Constraints

Constraint: no runtime enablement.

Constraint: no external calls.

Constraint: no credentials/tokens.

Constraint: no sandbox execution.

Constraint: no privileged bypass.
