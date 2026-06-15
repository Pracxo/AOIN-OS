# ADR 0011: Goal and Task Lifecycle Control Plane

## Decision

AION Brain owns generic goal records, cognitive task records, task runs,
schedule metadata, lifecycle transitions, policy gates, audit semantics, and
visual telemetry for lifecycle activity.

## Reason

The Brain needs to hold goals over time without becoming a vertical workflow
engine. A generic lifecycle control plane lets future modules request goals,
tasks, and schedule metadata through AION-owned contracts while preserving a
single governed state machine.

## Constraints

- No domain-specific workflow logic lives in Brain core.
- No module owns Brain lifecycle state.
- Task runs are explicit and policy-gated.
- Dry-run task execution has no external side effects.
- Schedule support is metadata only in v0.1.
- Temporal remains a future adapter and is not imported.
- Lifecycle events publish through NATS best-effort, but Postgres persistence is
  canonical.

## Consequences

Future modules can plug into AION lifecycle management through events and
capability contracts without changing Brain public APIs. Durable workflow
engines can be added later behind adapters, but they will not replace AION
contracts or lifecycle authority.
