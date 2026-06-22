# ADR 0020: Graphiti Temporal Knowledge Graph Adapter

## Decision

AION Brain adds an optional Graphiti temporal knowledge graph adapter behind
`GraphMemoryAdapter`. Postgres graph memory remains the default canonical graph
ledger.

## Reason

AION needs a stable graph memory contract before adopting external temporal
graph engines. Graphiti can later provide richer temporal graph indexing and
episode recall, but Brain public APIs must remain independent of Graphiti
internals.

## Constraints

- Graphiti is disabled by default.
- The optional Graphiti package is not required for normal tests or local boot.
- Direct Graphiti imports are limited to `memory/graphiti_compat.py`.
- No Graphiti client, backend handle, row, or vendor type may cross public Brain
  APIs.
- No external model call is made for Graphiti when the model gateway is disabled.
- No domain-specific graph logic is introduced.

## Consequences

The kernel can select Graphiti by configuration, report adapter status, dry-run
or perform graph sync, and add generic temporal episodes. When Graphiti is
selected but unavailable, AION can fall open to Postgres graph memory if
configured. Future Graphiti package changes can be absorbed inside the compat
boundary without changing Brain contracts.
