# 0157: Self-Improvement Evaluation Authorization

Date: 2026-07-18

Status: Accepted

## Context

AION-166 implemented the governed self-improvement control plane under `AION-165-SI-0001`. That authorization is now consumed by PR 77 and merge commit `9a7105e31b8f6e56faf53bfb56e11eed75a01203`.

The next step is an immutable evaluation and benchmark plane that can compare candidate behavior against baseline evidence without letting candidate code rewrite source, alter its own benchmark, expose hidden holdout content, approve itself, create pull requests, deploy, or train model weights.

## Decision

AION-167 creates `authorization_transaction_id=AION-167-SI-0002` for AION-168 with `authorization_scope=immutable-self-improvement-evaluation-plane`.

The authorization covers:

- benchmark contracts
- baseline results
- candidate results
- multi-objective scoring
- hard safety gates
- immutable benchmark manifests
- holdout references
- statistical comparison
- evaluation provenance
- cost and latency accounting
- benchmark drift detection

The authorization keeps all mutating self-improvement effects disabled:

- `source_rewriting_enabled=false`
- `pull_request_creation_enabled=false`
- `automatic_approval_enabled=false`
- `benchmark_mutation_by_candidate_enabled=false`
- `holdout_disclosure_to_patch_generators_enabled=false`
- `production_deployment_enabled=false`
- `model_weight_training_enabled=false`

## Consequences

AION-168 may implement deterministic, dependency-free evaluation contracts and services. It may not create patches, mutate Git state, create pull requests, approve changes, deploy, train model weights, weaken holdout controls, or let quality gains offset safety failures.
