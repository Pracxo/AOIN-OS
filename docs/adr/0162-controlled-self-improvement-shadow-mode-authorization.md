# ADR 0162: Controlled Self-Improvement Shadow-Mode Authorization

## Status

Accepted for AION-177.

## Context

AION-176 reconciled post-merge evidence and AION-OE-001 concluded with
`OPERATOR_EVALUATION_PASS_RECOMMEND_SHADOW_MODE_AUTHORIZATION_REVIEW`. The
operator evaluation is evidence, not approval. A separate authorization is
required before any implementation task can begin.

## Decision

Create `AION-177-SI-0006` as the single active implementation authorization for
AION-178 controlled self-improvement shadow mode.

The authorization permits disabled, observation-only shadow-mode contracts,
pipeline, redacted evidence, budget enforcement, and operator review records. It
does not permit runtime self-improvement activation, source rewrite, Git writes,
pull request creation, automatic merge, production canary, deployment, provider
calls, connector calls, model-weight training, approval creation, self approval,
v0.2 tags, v0.2 releases, or movement of `aion-v0.1.0`.

## Consequences

AION-178 may implement only the bounded shadow-mode surfaces described by the
AION-177 evidence set. AION-177 remains non-reusable and must be consumed or
closed by AION-178 before any later activation decision.
