# Source Registry Implementation

AION-207 implements the AION-206-KI-0002 append-only source provenance registry core.

The implementation accepts validated AION-205 `ResearchEvidenceBundle` objects and projects them into immutable metadata-only registry envelopes for source snapshot digests, provenance references, citation references, lineage records, deduplication decisions, policy-decision payloads, and operator-review references.

Reuse decisions:

- Canonical JSON and SHA-256 fingerprinting reuse `aion_brain.contracts.knowledge_research.fingerprint_payload`.
- UTC timestamp, safe identifier, hex fingerprint, and protected-material validators reuse the AION-205 research contracts.
- AION-205 source snapshot, provenance, citation, lineage, deduplication, and evidence models remain the input contracts. They were not copied or replaced.
- The repository is an immutable in-memory adapter with pure simulated append. It creates no file, database, scheduler, worker, API route, CLI, SDK runtime surface, or startup registration.

Current state:

- `source_provenance_registry_implemented=true`
- `source_provenance_registry_state=implemented_append_only_in_memory_replay_persistent_write_disabled`
- `source_registry_runtime_enabled=false`
- `source_registry_persistent_write_enabled=false`
- `source_body_persistence_enabled=false`
- `claim_verification_enabled=false`
- `knowledge_promotion_enabled=false`
- `belief_mutation_enabled=false`
- `network_access_enabled=false`

AION-206-KI-0002 remains active, unconsumed, unexpired, and non-reusable pending AION-208 formal closeout.
