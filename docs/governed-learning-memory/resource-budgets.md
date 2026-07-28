# Governed Learning and Memory Resource Budgets

AION-221 authorizes bounded dry-run planning only.

| Limit | Value |
| --- | ---: |
| `maximum_promotion_requests_per_batch` | 100 |
| `maximum_candidates_per_request` | 100 |
| `maximum_lineage_references_per_candidate` | 500 |
| `maximum_source_references_per_candidate` | 100 |
| `maximum_claim_references_per_candidate` | 20 |
| `maximum_assessment_references_per_candidate` | 20 |
| `maximum_mesh_references_per_candidate` | 20 |
| `maximum_tool_session_references_per_candidate` | 20 |
| `maximum_approval_evidence_records_per_transaction` | 4 |
| `maximum_projection_records_per_transaction` | 100 |
| `maximum_versions_per_knowledge_identity` | 100 |
| `maximum_rollback_steps_per_transaction` | 50 |
| `maximum_compensation_steps_per_transaction` | 50 |
| `maximum_operator_review_items` | 100 |
| `maximum_in_memory_transactions` | 1000 |
| `maximum_query_results` | 1000 |
| `maximum_fixture_records` | 5000 |
| `maximum_fixture_bytes` | 4194304 |
| `maximum_concurrency` | 4 |
| `maximum_persistent_knowledge_writes` | 0 |
| `maximum_persistent_verified_knowledge_writes` | 0 |
| `maximum_cognitive_memory_writes` | 0 |
| `maximum_semantic_memory_writes` | 0 |
| `maximum_episodic_memory_writes` | 0 |
| `maximum_procedural_memory_writes` | 0 |
| `maximum_belief_creations` | 0 |
| `maximum_belief_mutations` | 0 |
| `maximum_automatic_knowledge_promotions` | 0 |
| `maximum_automatic_candidate_approvals` | 0 |
| `maximum_engagement_fact_promotions` | 0 |
| `maximum_engagement_confidence_effects` | 0 |
| `maximum_network_calls` | 0 |
| `maximum_search_provider_calls` | 0 |
| `maximum_connector_calls` | 0 |
| `maximum_model_provider_calls` | 0 |
| `maximum_actual_tool_executions` | 0 |
| `maximum_shell_commands` | 0 |
| `maximum_subprocess_executions` | 0 |
| `maximum_browser_actions` | 0 |
| `maximum_source_mutations` | 0 |
| `maximum_git_operations` | 0 |
| `maximum_runtime_created_pull_requests` | 0 |
| `maximum_runtime_created_approvals` | 0 |
| `maximum_deployments` | 0 |
| `maximum_model_weight_changes` | 0 |

All counters for persistent writes, memory writes, belief mutations, automatic promotions, network calls, tool executions, source mutations, Git operations, deployments, and model-weight changes are zero.

## AION-222 resource budgets

AION-222 implements the AION-221-GLM-0001 authorized promotion-planning core as deterministic, approval-bound, dry-run, in-memory, and write-disabled.

The implemented surface binds verified-knowledge candidates to complete lineage, validates externally supplied approval evidence, enforces separation of duties, revalidates eligibility and integrity, derives knowledge identity, detects duplicate and conflict conditions, plans append-only versions, prepares semantic, episodic, procedural, and belief-candidate projection plans, validates rollback and compensation, records immutable in-memory journal entries, and emits redacted operator review evidence.

This artifact does not authorize persistence. Persistent knowledge writes, verified-candidate persistence, semantic/episodic/procedural/cognitive-memory writes, belief creation or mutation, approval creation, automatic promotion, network access, runtime registration, production exposure, v0.2 tagging, and v0.2 release creation remain disabled.
