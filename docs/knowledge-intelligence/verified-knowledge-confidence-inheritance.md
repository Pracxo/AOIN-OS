# Verified Knowledge Confidence Inheritance

AION-217 implements the deterministic verified-knowledge candidate memory and engagement-learning candidate plane under AION-216-KI-0007. The implementation is immutable, redacted, synthetic-testable, and in-memory only.

Key controls:

- candidates remain reviewable evidence, not factual truth
- eligibility never creates approval or knowledge promotion
- confidence is inherited from upstream assessment, mesh, and tool-evidence caps
- confidence non-amplification is enforced by the minimum cap rule
- source identity, source independence, claim identity, valid time, jurisdiction, and version scope stay explicit
- corrections, retractions, supersession, unresolved contradiction, dissent, and optional tool-verification provenance stay preserved
- repository snapshots and exact queries are deterministic and non-persistent
- engagement metadata is non-factual and cannot alter confidence, source independence, coverage, freshness, contradiction state, policy, cognitive memory, beliefs, or model weights
- persistent verified-knowledge writes, automatic promotion, cognitive-memory writes, belief mutation, public-network access, real tool execution, API routes, CLI commands, background workers, and schedulers remain disabled

Current state flags: `verified_knowledge_memory_authorized=true`, `verified_knowledge_memory_implemented=true`, `verified_knowledge_memory_state=implemented_deterministic_in_memory_candidate_versioning_engagement_learning_persistent_write_disabled`, `engagement_learning_candidate_plane_authorized=true`, `engagement_learning_candidate_plane_implemented=true`, `verified_knowledge_runtime_enabled=false`, `persistent_verified_knowledge_write_enabled=false`, `automatic_verified_knowledge_promotion_enabled=false`, `cognitive_memory_write_enabled=false`, `belief_mutation_enabled=false`, `engagement_signal_as_fact_enabled=false`, `engagement_confidence_effect_enabled=false`, `public_network_fetch_enabled=false`, `actual_tool_execution_enabled=false`, `runtime_effect=false`.

AION-216-KI-0007 remains active, consumed=false, expired=false, reusable=false, pending AION-218 formal closeout.
