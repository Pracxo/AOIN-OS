# Source Provenance Registry Boundary

The AION-207 registry boundary is append-only metadata only. Source content remains untrusted evidence and source classification does not establish truth. Registry records may reference digests and citation identifiers, but they must not store full source bodies and must not make any claim-verification decision.

## Prohibited Runtime Effects

- `source_registry_runtime_enabled`: false
- `source_body_persistence_enabled`: false
- `full_source_content_repository_storage_enabled`: false
- `public_network_fetch_enabled`: false
- `search_provider_integration_enabled`: false
- `connector_integration_enabled`: false
- `model_provider_integration_enabled`: false
- `claim_verification_enabled`: false
- `automatic_claim_verification_enabled`: false
- `knowledge_promotion_enabled`: false
- `automatic_knowledge_promotion_enabled`: false
- `belief_mutation_enabled`: false
- `automatic_belief_creation_enabled`: false
- `background_crawler_enabled`: false
- `scheduled_research_enabled`: false
- `api_route_approved`: false
- `cli_runtime_command_approved`: false
- `sdk_runtime_resource_approved`: false
- `dependency_change_approved`: false
- `migration_approved`: false
- `github_workflow_change_approved`: false
- `source_mutation_enabled`: false
- `git_mutation_enabled`: false
- `real_pull_request_creation_enabled`: false
- `approval_creation_enabled`: false
- `automatic_merge_enabled`: false
- `production_deployment_enabled`: false
- `model_weight_training_enabled`: false
- `runtime_effect`: false
- `credential_use_enabled`: false
- `cookie_use_enabled`: false
- `authorization_header_use_enabled`: false
- `unrestricted_network_access_enabled`: false
- `private_network_access_enabled`: false
- `v02_tag_created`: false
- `v02_release_created`: false
