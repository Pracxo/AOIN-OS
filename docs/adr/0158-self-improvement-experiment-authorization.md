# ADR 0158: Self-Improvement Experiment Authorization

## Status

Accepted

## Context

AION-168 implemented the immutable self-improvement evaluation plane under `AION-167-SI-0002`. The next step needs a proposal and experiment engine that can transform observed weaknesses into bounded hypotheses and evidence without creating source changes or Git activity.

## Decision

Create `AION-169-SI-0003` as the active authorization for AION-170. The authorized scope is limited to failure-pattern intake, improvement hypotheses, regression-test proposals, experiment plans, baseline/candidate experiment execution, risk classification, evidence bundles, and approval-pending lifecycle records.

AION-170 is not authorized to mutate source, create commits, create branches, open pull requests, merge, deploy, train model weights, create a v0.2 tag, create a v0.2 release, or modify `aion-v0.1.0`.

## Consequences

- The experiment engine can prepare reviewable evidence and approval-pending proposals.
- Existing evaluation evidence remains a read-only input to experiments.
- Source-writing and Git operations remain outside scope until a later explicit authorization.
- Human approval and exact evidence binding remain required before any implementation patch can advance.
