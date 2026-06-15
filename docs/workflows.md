# Durable Workflows

AION Brain workflows are generic, durable records for long-running cognitive
work. They are not domain workflows and do not contain finance, trading, IT,
legal, healthcare, HR, procurement, or other vertical logic.

## Contracts

- `WorkflowDefinition` stores workflow metadata, trigger type, owner scope,
  retry policy, timeout, risk level, status, and ordered `WorkflowStep`
  records.
- `WorkflowRun` stores one run attempt, input, output, error, retry state, and
  embedded `WorkflowStepRun` records.
- `WorkflowHeartbeat` and `WorkflowWorkerRecord` record bounded local worker
  activity.
- `WorkflowEngineStatus` and `TemporalAdapterStatus` expose public readiness
  state without leaking vendor objects.

## Local Engine

The default adapter is `local`. It persists workflow state in the canonical
database and runs deterministic dry-runs by default. Controlled mode is still
policy-gated and does not create arbitrary shell or network execution paths.

Supported controls:

- create, read, activate, and disable workflow definitions
- run workflows in dry-run or controlled mode
- pause, resume, cancel, and retry workflow runs
- persist step attempts, lifecycle events, heartbeats, and worker records

## Scheduler And Worker

The scheduler and worker are disabled by default. They never start implicitly
when the API starts.

Explicit controls:

- `POST /brain/workflows/scheduler/tick`
- `POST /brain/workflows/worker/start-once`
- `./scripts/run-local-worker.sh`

Each worker call is bounded by `max_runs`. Tests use this bound to avoid
infinite loops.

## Temporal Boundary

Temporal is a future adapter boundary. `TemporalAdapter` and `TemporalCompat`
are the only workflow Temporal surfaces in v0.1. The optional SDK is not
required for the default stack or tests, and public Brain contracts remain
independent of Temporal internals.

## Policy

Workflow actions use the generic `workflow.*` policy vocabulary. Unknown
workflow actions fail closed. High and critical risk workflow work requires
approval before controlled execution.
