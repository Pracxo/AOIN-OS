# Source Provenance Registry Architecture

AION-206 authorizes AION-207 to implement an append-only source and provenance registry. AION-207 implements the registry as metadata-only, immutable, in-memory state with source snapshot digest references, provenance references, citation references, lineage records, deduplication decisions, policy-decision payloads, deterministic indexes, integrity reports, and operator review items. It must not persist source bodies, apply persistent registry writes, verify claims, promote knowledge, mutate beliefs, execute network fetches, or register runtime API, CLI, SDK, workflow, migration, connector, or model-provider surfaces.

Authorization transaction: `AION-206-KI-0002`. Scope: `append-only-immutable-source-snapshot-provenance-lineage-citation-registry-core`. Formal closeout: `AION-208`.
