# Claim Graph Operator Runbook

AION-209 implements the AION-208-KI-0003 immutable temporal claim-evidence graph core. The graph accepts explicit structured unverified claim assertions, binds them to AION-207 source-registry record IDs, models valid time, transaction time, jurisdiction, version scope, evidence roles, claim relations, structural conflict candidates, deterministic indexes, bounded exact queries, fixture replay, and integrity audit evidence.

## Boundary

- Program: `AION-KNOWLEDGE-INTELLIGENCE-001`
- Authorization: `AION-208-KI-0003`
- Implementation task: `AION-209`
- Formal closeout: `AION-210`
- Scope: `append-only-immutable-temporal-claim-evidence-provenance-jurisdiction-version-contradiction-graph-core`
- State: `implemented_append_only_in_memory_unverified_persistent_write_disabled`
- Runtime enabled: `false`
- Persistent graph writes enabled: `false`
- Maximum graph write batch: `0`

AION-209 does not extract claims automatically, parse source bodies, assign truth, calculate confidence, resolve contradictions, promote knowledge, mutate beliefs, call a network, create an API route, register a CLI, create a database, or write graph state.

## Evidence

The implementation is represented by strict Pydantic contracts, pure in-memory projection, deterministic fingerprints, immutable record envelopes, redacted diagnostics, and focused tests under `services/brain-api/tests/test_knowledge_claim_graph_*.py`.

Operator steps: run the focused AION-209 tests, run `./scripts/knowledge-intelligence-claim-graph-check.sh`, confirm runtime and persistence remain disabled, and route AION-210 for formal closeout.
