# v0.2 Identity Assertion Replay Protection No-Go

AION-164 keeps these states false or absent:

- `request_authentication_approved=false`
- `request_middleware_integration_approved=false`
- `actor_context_application_approved=false`
- `request_identity_context_application_approved=false`
- `runtime_implementation_approved=false`
- `runtime_enablement_guard_release_approved=false`
- `production_auth_runtime_enabled=false`
- `replay_protection_core_runtime_enabled=false`
- `replay_repository_runtime_registered=false`
- `raw_assertion_persistence_approved=false`
- `signature_persistence_approved=false`
- `verified_claim_persistence_approved=false`
- `external_calls_approved=false`
- `provider_discovery_approved=false`
- `jwks_network_fetch_approved=false`
- `new_dependency_approved=false`
- `new_package_manifest_added=false`
- `lockfiles_added=false`
- `migrations_added=false`
- `runtime_api_routes_added=false`
- `sdk_runtime_resource_added=false`
- `cli_runtime_command_added=false`
- `connector_runtime_enabled=false`
- `operator_write_execution_enabled=false`
- `module_activation_enabled=false`
- `sandbox_execution_enabled=false`
- `v02_tag_created=false`
- `v02_release_created=false`

The authorized implementation may persist only replay hashes and timestamps.
