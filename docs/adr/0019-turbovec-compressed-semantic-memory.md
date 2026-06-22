# ADR 0019: TurboVec Compressed Semantic Memory Adapter

## Decision

AION Brain adds optional TurboVec compressed semantic recall behind
`SemanticMemoryAdapter`. pgvector remains the default semantic adapter. TurboVec
is disabled by default, selected only by configuration, and loaded only through
`aion_brain.memory.turbovec_compat`.

## Reason

AION needs a path for compressed semantic recall without coupling Brain public
contracts to a vector engine. The adapter lets the Brain index canonical
`MemoryRecord` summaries into a compressed recall structure while preserving
Postgres as the canonical memory ledger.

## Consequence

Future deployments can enable TurboVec when the optional package is installed.
If TurboVec is selected but unavailable, the kernel can fall open to pgvector
when configured, or fail closed when fallback is disabled. Retrieval results
include AION-owned adapter metadata, not vendor objects.

## Constraints

TurboVec is an optional dependency group. No direct TurboVec import may appear
outside `memory/turbovec_compat.py`. TurboVec index metadata stores recall
pointers and hashes only; it does not store raw evidence and does not replace
canonical memory. No external network calls, model calls, domain-specific logic,
or frontend implementation are introduced by this adapter.
