# ADR 0006: Temporal Graph Memory Baseline

## Status

Accepted

## Decision

AION Brain v0.1 uses PostgreSQL as the local temporal graph memory baseline.
Graphiti may be enabled later as an optional adapter behind
`GraphMemoryAdapter`; see ADR 0020.

## Reason

PostgreSQL keeps local Docker development compatible with the existing Brain
stack and allows deterministic tests without requiring an external graph
service. AION can validate graph contracts, temporal semantics, policy gates,
scope filtering, and visual telemetry before introducing a specialized graph
engine.

## Consequence

AION owns graph contracts, provenance rules, memory scopes, temporal semantics,
and visual telemetry semantics. Graph engines only store and retrieve
relationships, so the engine can be replaced later without changing public
Brain contracts.

## Constraints

Postgres graph memory remains the default canonical baseline. The Brain must
call `GraphMemoryAdapter` and must not call Graphiti, Neo4j, FalkorDB,
Memgraph, or any graph engine directly. Graph memory remains generic and
domain-neutral.
