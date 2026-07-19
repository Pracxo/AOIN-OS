# Operator Evaluation Guide

This guide is the operator evaluation entry point after AION-175 merged. The
platform is ready for review as an implemented, disabled self-improvement
control plane.

## Review Steps

1. Inspect `docs/self-improvement/final-architecture.md` for the implemented component map.
2. Inspect `examples/self-improvement/final-readiness-report.json` for machine-readable readiness evidence.
3. Run `./scripts/self-improvement-runtime-hold.sh` to confirm autonomous runtime activation remains false.
4. Run `./scripts/self-improvement-final-check.sh` when a full local validation is required.
5. Review `docs/self-improvement/security-review.md` and `docs/self-improvement/known-limitations.md` before considering future activation work.

## Evaluation Questions

- Does the evidence show deterministic self-evaluation and immutable benchmark comparison?
- Are proposal generation, experiment execution, worktree creation, PR control, and merge control approval-bound?
- Does the canary plane remain simulation-only until an exact future approval enables production exposure?
- Are rollback decisions constrained to approved canary plans and explicit thresholds?
- Do adaptive-learning outputs remain data-only candidates rather than runtime source changes?
- Are protected core, holdout benchmark content, and test-integrity controls preserved?

## Non-Goals For This Review

This closeout does not approve production runtime self-improvement. It does not
approve model-backed patch generation, model-weight training, production canary
traffic, direct deployment, or autonomous merge. Those require a separate future
authorization.
