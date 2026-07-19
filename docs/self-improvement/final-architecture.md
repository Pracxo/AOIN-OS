# Governed Self-Improvement Final Architecture

AION-175 closes the governed self-improvement implementation track. The platform is implemented but disabled for autonomous runtime use. It can evaluate performance, produce bounded improvement proposals, run isolated experiments, prepare approval-bound source changes, simulate canaries, record outcomes, and roll back degrading candidates under an approved canary plan.

## Implemented Components

- Governance plane: lifecycle, risk, protected paths, approval binding, change budget, evidence, and audit contracts.
- Evaluation plane: immutable benchmark manifests, baseline/candidate bundles, hard safety gates, holdout protection, scoring, comparison, drift detection, cost, latency, and provenance.
- Experiment plane: observations, repeated failure patterns, bounded hypotheses, regression-test proposals, experiment plans, and approval-pending proposals.
- Rewrite plane: isolated worktrees, test-first evidence, disabled default patch generator, deterministic test patch generator, patch validation, diff hashing, sandbox evidence, Git branch control, PR adapter control, CI monitoring, merge control, and rollback metadata.
- Canary and adaptation plane: exact approval-bound canary plans, exposure budgets, monitoring thresholds, rollback decisions, outcome ledger, retrieval ranking candidates, case-based planning, strategy selection, preference learning, procedural skill evolution, and isolated integrated dry-run.

## Runtime State

The implementation state is `implemented_disabled`. Runtime self-improvement, runtime source rewrite, automatic merge, production canary, production deployment, production exposure, and model-weight training are all disabled. Human approval remains required for any source change, exact commit and diff hash binding remain required, and protected-core changes still require dual approval.

## Control Flow

1. Evaluation evidence identifies a repeated weakness.
2. Pattern intake produces a bounded failure pattern.
3. Hypothesis and regression-test proposal components create reviewable evidence.
4. Experiment execution compares baseline and candidate outcomes against immutable gates.
5. Isolated worktree controls prepare a test-first candidate.
6. Exact approval binds proposal ID, commit SHA, diff hash, benchmark fingerprint, rollback commit, and deployment scope.
7. PR and merge controllers operate only through explicit adapters and never push directly to `main`.
8. Canary simulation remains local and disabled by default.
9. Approved rollback thresholds can trigger rollback inside an already approved canary plan.
10. Outcome and learning ledgers record proposal, experiment, approval, PR, merge, canary, rollback, final outcome, and survival review evidence.

## Boundary

The platform does not approve its own source changes, does not bypass GitHub checks, does not weaken tests to pass a patch, does not modify protected governance controls through ordinary proposals, does not alter holdout benchmark content through generated patches, does not activate production self-rewrite, and does not create a v0.2 tag or release.
