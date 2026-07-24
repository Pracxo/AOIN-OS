# Source Provenance Registry Architecture

AION-206 authorizes AION-207 to implement an append-only source and provenance registry. AION-207 implements the registry as metadata-only, immutable, in-memory state with source snapshot digest references, provenance references, citation references, lineage records, deduplication decisions, policy-decision payloads, deterministic indexes, integrity reports, and operator review items. It must not persist source bodies, apply persistent registry writes, verify claims, promote knowledge, mutate beliefs, execute network fetches, or register runtime API, CLI, SDK, workflow, migration, connector, or model-provider surfaces.

Authorization transaction: `AION-206-KI-0002`. Scope: `append-only-immutable-source-snapshot-provenance-lineage-citation-registry-core`. Formal closeout: `AION-208`.


## AION-208 Knowledge Intelligence State

AION-208 completed read-only operator evaluation `AION-SPRE-001` for the AION-207 append-only source provenance registry. The registry remains metadata-only, in-memory, and persistent-write-disabled. `AION-206-KI-0002` is closed and non-reusable. `AION-208-KI-0003` is the sole active Knowledge Intelligence implementation authorization for AION-209. AION-209 may implement the temporal claim-evidence graph, but automatic claim extraction, truth decisions, confidence calculation, knowledge promotion, cognitive belief mutation, persistent graph writes, source-body storage, network access, source mutation, Git mutation, runtime PRs, automatic merge, deployment, and model training remain disabled.
