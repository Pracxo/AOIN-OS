# Production Auth Core Runtime Boundary

AION-152 keeps the production-auth runtime boundary closed.

AION-153 renews the same closed runtime boundary for the active
`AION-153-PA-0002` stabilization authorization. The authorization permits only
future disabled-core stabilization work and does not release runtime auth.

Disabled states:

- `login_endpoint_enabled=false`
- `logout_endpoint_enabled=false`
- `callback_endpoint_enabled=false`
- `credential_storage_enabled=false`
- `password_storage_enabled=false`
- `token_issuance_enabled=false`
- `token_storage_enabled=false`
- `session_creation_enabled=false`
- `session_storage_enabled=false`
- `cookie_issuance_enabled=false`
- `cookie_session_persistence_enabled=false`
- `external_identity_provider_enabled=false`
- `oauth_runtime_enabled=false`
- `oidc_runtime_enabled=false`
- `saml_runtime_enabled=false`
- `external_calls_enabled=false`
- `network_client_enabled=false`
- `provider_sdk_enabled=false`
- `runtime_api_routes_added=false`

The route table must not add `/production-auth`, `/auth/production`, login,
logout, callback, token, credential, OAuth, OIDC, or SAML runtime routes.
Existing local preview auth routes remain preview-only and are not converted
into production behavior.
