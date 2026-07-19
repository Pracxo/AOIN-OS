# Self-Improvement Benchmark Report

AION-175 confirms the immutable benchmark and evaluation plane is available for user evaluation.

## Benchmark Capabilities

- Benchmark manifests are fingerprinted and immutable.
- Baseline and candidate results are represented as separate evidence bundles.
- Hard gates require tests, security checks, policy checks, protected-boundary checks, holdout threshold success, no critical regression, and rollback plan presence.
- Quality gains cannot offset safety failures.
- Holdout content is protected from patch-generation paths.
- Drift reports and deterministic comparisons use standard-library logic.

## Current Validation Evidence

- AION-168 evaluation-plane tests remain in the full Brain API suite.
- AION-170 experiment-engine tests exercise baseline/candidate flow into approval-pending proposals.
- AION-172 rewrite-controller tests exercise benchmark fingerprint binding.
- AION-174 integrated dry-run records benchmark comparison completion before approval-pending evidence.

## Report Boundary

This report is readiness evidence. It does not change benchmark thresholds, disclose hidden holdout content, or authorize production self-improvement.
