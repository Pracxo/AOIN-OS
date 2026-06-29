# ADR 0098: Operator Action Write-Path Architecture

## Status

Accepted for AION-107 design scope.

## Context

AION already supports governed operator action requests, dry-run previews,
blockers, review records, role-aware filtering, local session previews,
dry-run action authorization, operator platform freeze gates, and connector
boundary design. It still intentionally has no operator action write execution.

The next architecture question is how a future write path should be bounded so
later implementation cannot treat a dry-run preview, review record, approval
record, model output, connector declaration, or local role as execution
authority.

## Decisions

- Decision: add write-path architecture design only.
- Decision: no write execution is implemented in AION-107.
- Decision: current system remains dry-run/request/review only.
- Decision: future write path requires approval, policy, audit, rollback,
  production auth, and connector boundary gates.

## Reason

AION needs write-path architecture before any execution capability.

## Consequences

Future write implementation must pass no-execution regression and release
gates before any execution path can be added.

Future work must prove production auth, role mapping, approval workflow,
connector boundary, sandbox boundary, policy actions, audit/provenance,
rollback design, dry-run evidence, CI/release gate, and operator training.

## Constraints

- Constraint: no execution.
- Constraint: no external calls.
- Constraint: no activation.
- Constraint: no privileged bypass.

## Non-goals

- no write API
- no tool execution
- no action proposal execution
- no controlled handoff execution
- no connector runtime
- no provider SDK
- no network client
- no production auth runtime
- no login/logout behavior
- no credential, token, cookie, or session persistence
- no frontend dependency
- no package file
- no migration
