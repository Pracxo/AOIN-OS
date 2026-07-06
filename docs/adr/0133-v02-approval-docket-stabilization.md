# ADR 0133: v0.2 Approval Docket Stabilization

## Status
Accepted for preview-only stabilization.

## Context
AION-141 created the approval docket preview, runtime approval review boundary, and implementation decision record guard. AION now needs the docket layer stabilized so future implementation decision records can be reviewed against a frozen evidence baseline without granting implementation approval.

## Decisions
- Decision: add v0.2 approval docket stabilization.
- Decision: freeze implementation decision records as unapproved planning records.
- Decision: add runtime approval review evidence baseline.
- Decision: add approval docket lifecycle evidence matrix.
- Decision: AION-142 does not approve implementation.
- Decision: approval docket stabilization approval remains false.
- Decision: approval docket item approval remains false.
- Decision: implementation decision record freeze approval remains false.
- Decision: implementation decision record approval remains false.
- Decision: runtime approval review approval remains false.
- Decision: future implementation still requires explicit approval records, ADRs, and gate evidence.
- Decision: no v0.2 release or tag is created.

## Reason
Reason: AION needs a stable approval docket baseline before any runtime implementation decision can be considered.

## Consequence
Consequence: future implementation candidates remain blocked until explicit approval records are created by a future task and all required gates pass.

## Constraints
- Constraint: no runtime enablement.
- Constraint: no external calls.
- Constraint: no credentials/tokens.
- Constraint: no sandbox execution.
- Constraint: no package or migration changes.
- Constraint: no API, SDK, or CLI implementation changes.
- Constraint: no privileged bypass.
