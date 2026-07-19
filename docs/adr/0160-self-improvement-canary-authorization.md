# ADR 0160: Self-Improvement Canary Authorization

## Status

Accepted

## Context

AION-172 implemented the approval-bound isolated source rewrite and PR-control plane under `AION-171-SI-0004`. The next step needs a disabled-by-default canary, rollback, outcome-ledger, and adaptive-policy plane that can evaluate approved changes after merge without enabling autonomous production activation.

## Decision

Create `AION-173-SI-0005` as the active authorization for AION-174. The authorized scope is limited to canary plans, exposure budgets, monitoring windows, automatic rollback under approved thresholds, improvement outcome ledger, retrieval-ranking optimization, case-based planning, bounded strategy selection, shadow-mode policy comparison, data-only procedural skill evolution, and a final integrated dry-run.

AION-174 is not authorized to enable production canary by default, permit unrestricted traffic exposure, train or modify model weights, modify protected core automatically, relax policy automatically, self-approve at runtime, autonomously activate production, create a v0.2 tag or release, or modify `aion-v0.1.0`.

## Consequences

- Canary and rollback behavior can be modeled only against exact approval bindings.
- Adaptive learning remains data-only, reversible, bounded, and approval-gated.
- Production canary activation remains disabled by default.
- Runtime self-approval, automatic policy relaxation, and autonomous production activation remain prohibited.
