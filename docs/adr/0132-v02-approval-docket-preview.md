# ADR 0132: v0.2 Approval Docket Preview

## Status
Accepted for preview-only planning.

## Context
AION-138 created the decision package preview, AION-139 stabilized decision packages and approval readiness, and AION-140 completed the decision package final review and runtime decision lock. AION now needs an approval docket boundary before runtime decisions can be considered.

## Decisions
- Decision: add v0.2 approval docket preview.
- Decision: AION-141 does not approve implementation.
- Decision: approval dockets and implementation decision records remain preview-only.
- Decision: approval docket item approval remains false.
- Decision: implementation decision record approval remains false.
- Decision: runtime approval review approval remains false.
- Decision: future implementation still requires explicit approval records, ADRs, and gate evidence.
- Decision: no v0.2 release or tag is created.

## Reason
Reason: AION needs an approval docket boundary before runtime decisions can be considered.

## Consequence
Consequence: future implementation candidates remain blocked until docketed evidence and explicit approval records exist.

## Constraints
- Constraint: no runtime enablement.
- Constraint: no external calls.
- Constraint: no credentials/tokens.
- Constraint: no sandbox execution.
- Constraint: no privileged bypass.
