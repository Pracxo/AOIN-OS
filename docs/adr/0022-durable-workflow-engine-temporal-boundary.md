# ADR 0022: Durable Workflow Engine and Temporal Boundary

## Status

Accepted.

## Context

AION Brain needs durable, policy-gated state for long-running cognitive work
before external workflow engines are introduced. The core must remain
domain-neutral and must not require Temporal for local development, tests, or
the default stack.

## Decision

AION Brain adds a local database-backed durable workflow engine in v0.1. The
local engine owns workflow definitions, workflow runs, step runs, retries,
heartbeats, worker records, and workflow lifecycle events through AION-owned
contracts.

The local scheduler and local worker are explicit one-shot controls. They do
not start automatically during API startup or kernel boot.

Temporal is represented only as an optional future adapter boundary. The
`TemporalAdapter` returns AION contracts, and `TemporalCompat` confines optional
SDK lookup. The Temporal SDK is not a required dependency.

## Consequences

The Brain can persist and inspect durable workflow state immediately while
remaining deterministic by default. Future Temporal integration can replace or
augment the local engine without changing public workflow contracts.

Workflow execution remains generic. No finance, trading, IT, legal,
healthcare, HR, procurement, or other vertical workflow logic belongs in Brain
core.

## Constraints

- Workflow APIs must pass policy gates.
- Dry-run remains the default run mode.
- Workers and schedulers must be invoked explicitly.
- Public APIs must never expose Temporal SDK objects, worker internals, queue
  clients, database rows, or shell execution handles.
- Temporal integration must remain optional and disabled by default.
