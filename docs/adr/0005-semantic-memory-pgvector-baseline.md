# ADR 0005: Semantic Memory pgvector Baseline

## Decision

AION Brain v0.1 uses pgvector as the first working local semantic memory
adapter. TurboVec remains behind the same adapter boundary as a future
compressed semantic recall engine.

## Reason

pgvector works inside the default Docker stack and can share Postgres with the
canonical `MemoryRecord` metadata store. This keeps local development and tests
simple while giving AION a real semantic recall path.

## Consequence

AION owns semantic memory contracts, memory policy, scopes, grounding,
retrieval semantics, audit, and telemetry. Vector engines only provide recall,
so AION can swap pgvector for TurboVec or another engine later without changing
public Brain contracts.

## Constraints

No external embedding providers are used in v0.1. The `HashEmbeddingAdapter` is
deterministic and local. It is a development wiring baseline, not
production-grade intelligence.

TurboVec is not imported and no TurboVec dependency is added in v0.1.
