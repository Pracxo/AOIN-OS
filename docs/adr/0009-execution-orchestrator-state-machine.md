# ADR 0009: Execution Orchestrator and Plan Step State Machine

## Status

Accepted for AION Brain v0.1.

## Decision

AION Brain adds `ExecutionOrchestrator` and a plan step state machine for
explicit plan execution. Thinking and execution are separate: `/brain/think`
creates a trace and reports execution readiness, while `/brain/execute` runs a
supplied plan.

`dry_run` is the default execution mode. `controlled` mode is limited to safe
internal generic Brain steps. Temporal remains a future durable workflow adapter
behind `ExecutionAdapter`.

## Reason

Separating thinking from execution prevents accidental side effects and keeps
every action policy-gated, auditable, and replayable. The state machine gives
AION clear statuses for pending, running, completed, blocked, waiting for
approval, failed, and cancelled work.

## Constraints

- No external side effects in v0.1.
- No shell, browser, MCP, tool SDK, model provider, or Temporal SDK execution.
- No domain execution logic in Brain core.
- Capability invocation is policy-gated and returns structured
  `not_implemented` until future module runtimes exist.

## Consequences

AION can later plug in durable workflow engines and module runtimes without
changing public Brain contracts. Execution runs, step runs, approval
checkpoints, and capability invocation records are audit-ready from the first
version.
