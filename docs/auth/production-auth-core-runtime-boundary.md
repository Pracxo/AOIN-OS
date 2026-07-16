# Production Auth Core Runtime Boundary

AION-152 keeps the production-auth runtime boundary closed.

AION-153 renews the same closed runtime boundary for the active
`AION-153-PA-0002` stabilization authorization. The authorization permits only
future disabled-core stabilization work and does not release runtime auth.

## AION-154 Runtime Boundary

AION-154 stabilization does not release the runtime guard. The runtime boundary
continues to require `production_auth_runtime_enabled=false`,
`runtime_no_go_status=true`, `runtime_implementation_approved=false`,
`runtime_enablement_guard_release_approved=false`, and no login/logout/callback/
OAuth/OIDC/SAML/token/session/credential/production-auth route.

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

## AION-155 Request Boundary Hold

AION-155 keeps the production-auth runtime boundary closed. The new
authorization permits future AION-156 observe-only disabled request-state
integration only. Identity verification, authenticated requests, Authorization
header parsing, cookie parsing, credential verification, token parsing, session
creation, cookie issuance, external identity providers, external calls, runtime
API routes, and runtime guard release remain prohibited.
# AION-156 Request Identity Runtime Hold

The request identity boundary does not release any production-auth runtime
guard. Identity verification, authenticated requests, Authorization header
parsing, Cookie parsing, credentials, passwords, tokens, sessions, providers,
external calls, and auth routes remain disabled or absent.
