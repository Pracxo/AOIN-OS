# 0059: Run Supervision, Cancellation Gate, Timeout Policy, and Compensation Planner

## Status

Accepted

## Context

AION can propose actions and hand them off to governed target systems. A
handoff is not completion, a running target is not success, and a cancelled run
is not compensation. Operators need one Brain-owned way to observe handed-off
runs, request manual control, identify stalled or timed-out runs, and prepare
compensation plans without taking ownership of target execution semantics.

## Decision

AION Brain adds Run Supervision, Cancellation Gate, Timeout Policy, and
Compensation Planner contracts and services.

Run Supervision observes target systems but does not own execution. Target
systems remain authoritative for their own lifecycle state.

Control requests are manual and dry-run by default. Controlled handoff remains
disabled unless runtime configuration, policy, risk, autonomy, and approval
gates allow it.

Timeout policies detect and report stalled or timed-out runs. They do not
auto-cancel in v0.1.

Compensation plans do not execute themselves. Conversion to action proposals is
an explicit review path, not remediation.

## Consequences

Operators can detect stalled, failed, and timed-out runs without bypassing
target systems. The Brain can produce status samples, control requests,
timeout blockers, compensation plans, reports, telemetry, and operator queue
items while preserving target subsystem ownership.

## Constraints

- No background supervisor in v0.1.
- No automatic remediation.
- No automatic cancellation.
- No automatic compensation execution.
- No external calls.
- No domain-specific compensation logic in Brain core.
