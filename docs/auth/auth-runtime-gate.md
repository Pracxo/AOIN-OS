# Auth Runtime Gate

The auth runtime gate is the AION-099 status authority for disabled production
auth runtime flags.

The gate reports:

- `production_auth_enabled=false`
- `auth_runtime_enabled=false`
- `external_identity_provider_enabled=false`
- `credentials_enabled=false`
- `token_issuance_enabled=false`
- `cookie_issuance_enabled=false`
- `session_persistence_enabled=false`
- `login_endpoint_enabled=false`
- `logout_endpoint_enabled=false`

The only enabled preview flags are mock claims preview and actor mapping
preview. These do not authenticate a user, do not authorize actions, and do not
create persistent state.

If a future task attempts to turn any production auth flag on, the contract
validation and diagnostics are expected to fail closed before the runtime can be
treated as ready.
