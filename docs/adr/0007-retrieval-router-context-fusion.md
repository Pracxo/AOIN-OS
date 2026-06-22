# ADR 0007: Retrieval Router and Context Fusion

## Status

Accepted

## Decision

AION Brain adds `RetrievalRouter` between memory systems and the
`ContextCompiler`. AION Brain also adds `ContextFusionEngine` for deterministic
context assembly.

## Reason

The Brain now has lexical memory, semantic memory, graph memory, capabilities,
traces, evaluation, and learning signals. Pulling these directly inside the
Context Compiler would spread retrieval rules across the codebase and increase
context pollution risk. A dedicated router keeps policy gates, source
selection, ranking, deduplication, persistence, and telemetry in one Brain-owned
layer.

## Consequence

Future memory engines plug in as candidate sources. AION owns retrieval
contracts, source fusion, scoring, policy constraints, and telemetry semantics.
The Context Compiler consumes `ContextBundle` rather than vendor-specific
storage responses.

## Constraints

v0.1 uses deterministic scoring and no LLM summarization. Retrieval and fusion
must remain generic and domain-neutral. No domain-specific retrieval logic is
allowed.
