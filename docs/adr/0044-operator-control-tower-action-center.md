# ADR 0044: Operator Control Tower and Action Center

## Status

Accepted.

## Decision

AION adds an Operator Control Tower backend API.

The Control Tower is read-mostly. It may aggregate local state, create local
snapshots, create acknowledgements, expose runbook links, and expose generic
action recommendations.

Acknowledgements do not resolve source issues.

No frontend is implemented in v0.1.

## Reason

AION needs one local operational view before broader use. Operators need a
single backend contract for readiness, degraded components, pending actions,
queues, snapshots, and runbook links.

## Consequences

Future UI work can consume Operator contracts instead of querying subsystem
internals directly.

The Operator Control Tower must stay generic and backend-only.

## Constraints

- No automatic remediation.
- No action execution.
- No production auth in this task.
- No external service calls.
- No domain-specific operations.
