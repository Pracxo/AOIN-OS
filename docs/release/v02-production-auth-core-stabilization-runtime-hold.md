# v0.2 Production Auth Core Stabilization Runtime Hold

The AION-154 runtime hold preserves the AION-152 disabled implementation and the
AION-153 stabilization authorization boundary.

Required state:

- `runtime_guard_hold_active=true`
- `runtime_no_go_status=true`
- `production_auth_core_implemented=true`
- `production_auth_core_state=implemented_disabled`
- `production_auth_runtime_enabled=false`
- `runtime_implementation_approved=false`
- `runtime_enablement_guard_release_approved=false`
- `login_endpoint_enabled=false`
- `logout_endpoint_enabled=false`
- `callback_endpoint_enabled=false`
- `credential_storage_enabled=false`
- `password_storage_enabled=false`
- `token_issuance_enabled=false`
- `token_storage_enabled=false`
- `session_creation_enabled=false`
- `session_storage_enabled=false`
- `external_identity_provider_enabled=false`
- `external_calls_enabled=false`
- `runtime_api_routes_added=false`
- `v02_tag_created=false`
- `v02_release_created=false`

`./scripts/production-auth-core-stabilization-runtime-hold.sh` may invoke the
full repository check once during direct local execution. It defers the full
check when called from pytest or another aggregate gate.
