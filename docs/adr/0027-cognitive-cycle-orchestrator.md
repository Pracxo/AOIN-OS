# ADR 0027: Cognitive Cycle Orchestrator

## Status

Accepted

## Decision

AION Brain v0.1 adds a Cognitive Cycle Orchestrator for manual operating
rhythms: wake, active, review, sleep consolidation, maintenance, and shutdown.
Cycles are AION-owned contracts and ledgers, not scheduler jobs or background
workers.

## Reason

AION needs a safe way to review, consolidate, and maintain Brain state before
stronger autonomy exists. Manual cycles provide deterministic structure for
attention review, working-memory cleanup, memory governance, observability, and
kernel self-checks while preserving human control.

## Constraints

- Cycles are manual-only in v0.1.
- `dry_run` is the default mode.
- Controlled cycles require approval by default.
- No automatic background cycle runner is enabled.
- Sleep consolidation does not hard-delete memory.
- Sleep consolidation does not auto-promote skills.
- Cycles do not call models, invoke external services, or encode
  domain-specific logic.

## Consequences

Future UI or operator tooling can trigger safe cycles through stable Brain API
contracts. Future scheduling can be added later behind policy, autonomy, and
approval gates without changing the public cycle contracts.

