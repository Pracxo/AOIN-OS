# 0135: v0.2 Runtime Approval Board Preview

## Status

Accepted for preview boundary.

## Context

AION-141 created the approval docket preview. AION-142 stabilized the approval
docket. AION-143 completed the approval docket final review and runtime
approval lock. AION-144 defines how future runtime approval board decisions,
approval vote records, and go/no-go ledger entries are previewed before
implementation approval can be considered.

## Decision

- Decision: add v0.2 runtime approval board preview.
- Decision: AION-144 does not approve implementation.
- Decision: runtime approval board, approval vote records, and go/no-go ledger remain preview-only.
- Decision: runtime approval board decision approval remains false.
- Decision: approval vote record approval remains false.
- Decision: go/no-go ledger implementation go remains false.
- Decision: runtime approval lock release approval remains false.
- Decision: future implementation still requires explicit approval records, ADRs, and gate evidence.
- Decision: no v0.2 release or tag is created.

## Reason

- Reason: AION needs a runtime approval board preview before any runtime approval decision can be considered.

## Consequence

- Consequence: future runtime candidates remain blocked until approval board, vote record, and go/no-go evidence exists and explicit approval records are created.

## Constraints

- Constraint: no runtime enablement.
- Constraint: no external calls.
- Constraint: no credentials/tokens.
- Constraint: no sandbox execution.
- Constraint: no privileged bypass.

## Non-Goals

AION-144 does not enable connector runtime, operator write execution, production
auth, module activation, external calls, credential storage, token storage,
sandbox execution, package files, migrations, runtime API execution routes, SDK
runtime resources, or CLI command implementations.
