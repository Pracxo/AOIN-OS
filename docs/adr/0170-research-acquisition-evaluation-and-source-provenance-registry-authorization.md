# ADR 0170: Research Acquisition Evaluation and Source Provenance Registry Authorization

## Status

Accepted for AION-206.

## Context

AION-205 implemented the controlled research-acquisition core under `AION-204-KI-0001`. AION-206 evaluated that implementation with `AION-RAE-001`, including corrective PR #117 for the evaluation-discovered local fixture symlink boundary.

## Decision

The evaluation passed. `AION-204-KI-0001` is closed as consumed, inactive, expired, and non-reusable. `AION-206-KI-0002` authorizes AION-207 to implement an append-only source/provenance registry core only. AION-206 adds no AION-207 runtime source.

## Consequences

Research runtime, public network fetch, source body persistence, claim verification, knowledge promotion, belief mutation, external provider integration, Git mutation, PR creation, approval creation, merge, deployment, package, migration, API, CLI, SDK, workflow, tag, and release effects remain disabled.
