# ADR 0028: Event Reaction Router Subscription Control Plane

## Status

Accepted.

## Decision

AION Brain v0.1 adds a backend Event Reaction Router that converts persisted
`AIONEvent` records into generic, auditable reaction dispatches.

The router owns:

- Event subscription contracts.
- Deterministic trigger matching.
- Dispatch records.
- Reaction action records.
- Dead-letter records.
- Bounded replay.
- Router telemetry.

## Reason

AION needs a safe way to react to normalized events in real time without adding
a background worker, domain-specific workflow logic, or uncontrolled external
execution. Subscriptions let future modules declare interest in generic event
patterns while AION Brain keeps policy, autonomy, risk, approval, audit, and
telemetry control.

## Constraints

- No background event consumer in v0.1.
- Automatic intake dispatch is disabled by default.
- Dry-run is the default reaction mode.
- Controlled reactions must pass policy, autonomy, risk, and approval gates.
- Workflow, cognitive-cycle, and capability targets remain dry-run unless
  explicit metadata allows controlled behavior.
- No domain-specific subscription targets or trigger logic.
- No external network calls are introduced by the router.
- Public APIs return AION contracts only.

## Consequences

Future AION modules can queue reactions through generic event subscriptions
without bypassing Brain governance. Failed controlled actions become dead
letters that can be inspected, resolved, or replayed through a bounded
policy-gated API. A future frontend can visualize subscriptions, dispatches,
reactions, blocks, and dead letters through the existing Visual Brain
Projection layer.
