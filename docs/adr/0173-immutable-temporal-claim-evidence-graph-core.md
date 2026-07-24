# 0173: Immutable Temporal Claim-Evidence Graph Core

## Status

Accepted for AION-209 implementation under `AION-208-KI-0003`.

## Context

AION-207 registers immutable source metadata but deliberately does not model claims or verify facts. AION-208 authorized a bounded graph layer so future evaluation can reason about unverified claims, evidence bindings, time, jurisdiction, versions, relations, and structural conflict candidates without enabling truth, confidence, knowledge promotion, runtime activation, or persistence.

## Decision

Implement an immutable temporal claim-evidence graph core in Brain API contracts and Knowledge Intelligence modules. The graph uses explicit unverified claim assertions, typed object values, source-registry evidence bindings, valid time, transaction time, jurisdiction and version scope, relation edges, conservative structural conflict candidates, append-only record envelopes, deterministic indexes, bounded exact queries, fixture replay, integrity audit, and redacted operator-review evidence.

## Constraints

- Authorization: `AION-208-KI-0003`
- Scope: `append-only-immutable-temporal-claim-evidence-provenance-jurisdiction-version-contradiction-graph-core`
- Persistent graph write batch: `0`
- Runtime activation: disabled
- Claim extraction, truth decisions, confidence, contradiction resolution, knowledge promotion, and belief mutation: disabled
- Source-body parsing and storage: disabled
- Network, API, CLI, scheduler, worker, database, SDK runtime surface, Git mutation, PR creation, merge, deployment, and model training: disabled

## Consequences

AION-209 gives AION OS a deterministic representation layer for explicit unverified claims while preserving historical assertions and disabled runtime boundaries. AION-210 must evaluate this implementation and decide whether any future epistemic truth-engine authorization may proceed.
