# ADR 0088: Dry-Run Action Authorization Enforcement

## Status

Accepted for AION-097.

## Context

AION-092 introduced governed operator action requests, dry-run previews,
blockers, and review records. AION-094 through AION-096 added local auth,
read-only session context, and the role permission proof matrix. Operator
action requests now need an enforceable dry-run authorization layer before any
future write path exists.

## Decision

AION adds dry-run action authorization enforcement for governed operator
actions.

Authorization can allow only dry-run preview creation or review record
creation. Authorization never allows execution, activation, writes, external
calls, credential storage, session persistence, or privileged bypass.

Every decision checks role matrix permission, local session boundary, policy,
action type, target type, dry-run mode, and safety blockers.

## Consequences

Future write authorization must extend this model without weakening the
dry-run guarantees. Denied decisions remain visible as blockers or decision
records. No action execution adapter, activation path, external provider, or
new migration is added in AION-097.
