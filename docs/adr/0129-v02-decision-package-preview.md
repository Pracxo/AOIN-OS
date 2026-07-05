# 0129: v0.2 Decision Package Preview

## Status

Accepted

## Context

AION-137 stabilized the v0.2 review board and froze review routing as
planning-only decision-readiness evidence. The next planning step needs a
single decision package preview that bundles the evidence a future approval
workflow will inspect.

## Decision

Decision: add v0.2 decision package preview.

Decision: AION-138 does not approve the decision package.

Decision: approval readiness remains evidence only.

Decision: decision package approval remains false.

Decision: approval readiness approved remains false.

Decision: review board, routing, reviewer sign-off, submission, queue, request,
proposal, workstream, backlog, and runtime implementation approvals remain
false.

Decision: future runtime implementation still requires explicit approval records, ADRs, and gate evidence.

Decision: no v0.2 release or tag is created.

## Consequences

The repository gains a stable approval-readiness evidence bundle, state model,
runtime decision boundary, evidence matrix, no-go register, checklist, static
console panels, and local gates. The package is useful for future governance
review but cannot enable runtime work by itself.

## Constraints

- Constraint: no runtime enablement.
- Constraint: no external calls.
- Constraint: no credentials/tokens.
- Constraint: no sandbox execution.
- Constraint: no privileged bypass.
- Constraint: no package files.
- Constraint: no migrations.
- Constraint: no API runtime execution routes.
- Constraint: no SDK or CLI implementation changes.
