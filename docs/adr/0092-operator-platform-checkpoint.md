# 0092: Operator Platform Checkpoint

## Status

Accepted.

## Context

AION-089 through AION-100 created the static local Operator Console, read-only
module and provider dashboards, governed operator action previews, local auth
and session previews, role-aware filtering, dry-run authorization evidence,
production auth architecture, disabled auth runtime prototype, and UI release
gate.

AION needs a stable operator platform baseline before further UI, auth,
activation, connector, or write-path work is planned.

## Decision

Create an operator platform checkpoint after AION-100.

The checkpoint is documentation and evidence only. The static console remains
local, read-only, dependency-free, and build-free. Auth remains disabled or
mock-only. Write, activation, execution, provider, and external call controls
remain absent.

## Reason

AION needs one verified baseline that proves the Operator Platform phase is
closed safely before the next phase begins.

## Consequences

The next phase starts from a verified checkpoint. Future UI, auth, activation,
connector, or write-path work must preserve the checkpoint or add a new ADR and
gate before changing its boundaries.

## Constraints

- No runtime subsystem.
- No frontend dependency.
- No production auth.
- No privileged bypass.
- No login/logout behavior.
- No token or cookie issuance.
- No persisted sessions.
- No external identity provider runtime.
- No write path.
- No activation path.
- No execution path.
- No provider call path.
- No external call path.
