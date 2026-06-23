# 0083: Governed Operator Actions Dry-Run Only

## Status

Accepted.

## Decision

AION adds governed operator action requests as dry-run records.

Action requests are dry-run only. Previews do not execute. Reviews do not
execute. Execution, external calls, and activation remain disabled.

## Reason

Operators need a safe action-request workflow before governed writes or runtime
execution can be considered. The system should expose action intent, required
policy context, blockers, and review outcomes without adding execution risk.

## Consequence

Future console work can show action intent, blockers, and review records. The
current implementation creates local metadata, audit/provenance records, and
visual telemetry only.

## Constraints

- No execution.
- No external calls.
- No activation.
- No privileged bypass.
- No runtime route registration.
- No frontend dependency.
