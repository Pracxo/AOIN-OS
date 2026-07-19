# ADR 0159: Self-Improvement Rewrite Authorization

## Status

Accepted

## Context

AION-170 implemented the proposal and experiment engine under `AION-169-SI-0003`. The next step needs an isolated source-rewrite and PR-control plane that can prepare a patch workflow while preserving human approval, exact evidence binding, and runtime disablement.

## Decision

Create `AION-171-SI-0004` as the active authorization for AION-172. The authorized scope is limited to ephemeral Git worktrees, bounded file edits, test-first patch workflow, sandbox execution, exact diff hashing, exact commit approval binding, task branches, commits, PR creation, approved merge control, rollback commits, and GitHub CI monitoring.

AION-172 is not authorized to write directly to main, force push, self-approve, modify protected core under ordinary approval, change dependencies without exact authorization, weaken tests, mutate holdout data, merge automatically without approval, deploy to production, modify model weights, create a v0.2 tag or release, or modify `aion-v0.1.0`.

## Consequences

- Source rewrite work can be modeled and tested in isolated worktrees.
- PR and merge controls must remain approval-bound to exact commit and diff evidence.
- Production GitHub calls remain disabled unless explicitly configured later.
- Autonomous runtime self-rewrite, automatic merge, production deployment, and model-weight training remain disabled.
