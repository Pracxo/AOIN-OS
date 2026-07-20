# ADR 0163: Controlled Self-Improvement Shadow-Mode Plane

## Status

Accepted for AION-178.

## Context

AION-177 created AION-177-SI-0006 as the single active implementation
authorization for a controlled self-improvement shadow plane. The authorization
permits read-only observation, deterministic evaluation, failure-pattern mining,
bounded hypotheses, regression-test specifications, shadow proposals, operator
review items, evidence, budgets, redaction, retention, deterministic replay, and
operator-supplied output.

## Decision

Implement an operator-invoked Python API only. The plane uses explicit
manifests, injected read-only adapters, immutable Pydantic contracts, canonical
fingerprints, zero side-effect budgets, and bounded per-run concurrency. The
runtime remains disabled and unregistered.

## Consequences

AION-178 provides reviewable evidence but creates no active runtime influence.
Formal authorization closeout and shadow-evaluation decision remain assigned to
AION-179. Source rewriting, Git mutation, real PR creation, approval creation,
merge, canary, deployment, active-learning promotion, and model-weight training
remain prohibited.
