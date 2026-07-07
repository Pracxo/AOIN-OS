# 0138: v0.2 Implementation Authorization Preview

## Status

Accepted

## Context

AION-146 closed the runtime approval board layer and locked the implementation
go/no-go ledger to no-go. The next pre-implementation planning step is to define
the explicit authorization record shape and runtime enablement guard boundary
that future runtime candidates must satisfy.

## Decision

- Decision: add v0.2 implementation authorization preview.
- Decision: AION-147 does not approve implementation.
- Decision: explicit approval records and runtime enablement guards remain preview-only.
- Decision: implementation authorization approval remains false.
- Decision: explicit approval record approval remains false.
- Decision: runtime enablement guard release approval remains false.
- Decision: future implementation still requires explicit approval records, ADRs, and gate evidence.
- Decision: no v0.2 release or tag is created.

## Reason

AION needs an explicit authorization schema and runtime guard boundary before
implementation approval can be considered.

## Consequence

Future runtime candidates remain blocked until authorization records and guard
release evidence are complete and explicitly approved.

## Constraints

- Constraint: no runtime enablement.
- Constraint: no external calls.
- Constraint: no credentials/tokens.
- Constraint: no sandbox execution.
- Constraint: no privileged bypass.
