# Source Provenance Registry Resource Budgets

AION-206 sets the AION-207 source registry authorization budgets below. AION-207 keeps the persistent write batch at zero. Network, runtime write, claim verification, knowledge promotion, belief mutation, Git, approval, deployment, and model-provider budgets are all zero.

- `maximum_registry_records_per_plan`: `100`
- `maximum_record_envelope_bytes`: `8192`
- `maximum_metadata_bytes_per_record`: `4096`
- `maximum_lineage_edges_per_record`: `20`
- `maximum_citation_references_per_record`: `20`
- `maximum_registry_write_batch`: `0`
- `maximum_persisted_source_body_bytes`: `0`
- `maximum_repository_source_body_bytes`: `0`
- `maximum_claim_verifications`: `0`
- `maximum_knowledge_promotions`: `0`
- `maximum_belief_mutations`: `0`
- `maximum_network_calls`: `0`
- `maximum_git_operations`: `0`
- `maximum_runtime_created_pull_requests`: `0`
- `maximum_approvals_created_by_runtime`: `0`
- `maximum_background_crawls`: `0`
- `maximum_search_provider_calls`: `0`
- `maximum_connector_calls`: `0`
- `maximum_model_provider_calls`: `0`


## AION-208 Knowledge Intelligence State

AION-208 completed read-only operator evaluation `AION-SPRE-001` for the AION-207 append-only source provenance registry. The registry remains metadata-only, in-memory, and persistent-write-disabled. `AION-206-KI-0002` is closed and non-reusable. `AION-208-KI-0003` is the sole active Knowledge Intelligence implementation authorization for AION-209. AION-209 may implement the temporal claim-evidence graph, but automatic claim extraction, truth decisions, confidence calculation, knowledge promotion, cognitive belief mutation, persistent graph writes, source-body storage, network access, source mutation, Git mutation, runtime PRs, automatic merge, deployment, and model training remain disabled.
