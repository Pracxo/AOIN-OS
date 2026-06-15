# ADR 0014: Evidence Vault and Source Grounding

## Status

Accepted

## Context

AION Brain has memory, graph memory, retrieval, reasoning, planning, execution,
goals, tasks, modules, skills, identity, and policy. Stronger reasoning and
future autonomy require a grounding layer that preserves source material and
connects Brain outputs back to evidence.

## Decision

AION Brain will add an Evidence Vault and Source Grounding layer. The Brain
owns evidence contracts, content hash semantics, chunk records, evidence links,
source provenance, policy gates, grounding claims, audit semantics, and visual
telemetry semantics.

v0.1 supports text evidence and metadata-only content references. Text evidence
is content-addressed with deterministic SHA-256 hashes over normalized text and
split into deterministic chunks. Metadata-only content references are stored as
records but are not fetched.

MinIO remains a future adapter placeholder. Local and in-memory object stores
exist behind AION-owned `ObjectStoreAdapter` boundaries, and public contracts
remain independent of object-store internals.

## Constraints

- No URL fetch, PDF parsing, OCR, binary upload handling, or external object
  storage integration in v0.1.
- No external AI service calls.
- No domain-specific evidence logic.
- Grounding is deterministic and does not claim absolute truth.
- Memory, graph memory, retrieval, and reasoning may recall, but evidence must
  ground.

## Consequences

Memory and reasoning can reference evidence IDs and chunk IDs. Retrieved
context, prompt packets, evaluations, and visual telemetry can preserve source
references. Future object storage can be added behind adapters without changing
AION public contracts.
