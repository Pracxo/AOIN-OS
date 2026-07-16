# Request Identity Runtime Boundary

Status: runtime guard hold active.

The AION-156 request identity boundary is observe-only and disabled by default.
It may attach an anonymous disabled context only when
`AION_PRODUCTION_AUTH_REQUEST_BOUNDARY_ENABLED=true`; even then it performs no
authentication and has zero authorization effect.

## Prohibited Runtime Capabilities

- `authorization_header_parsing_enabled=false`
- `cookie_parsing_enabled=false`
- `credential_verification_enabled=false`
- `password_verification_enabled=false`
- `token_parsing_enabled=false`
- `token_issuance_enabled=false`
- `token_storage_enabled=false`
- `token_refresh_enabled=false`
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

## Surface Restrictions

No login, logout, callback, token, session, credential, production-auth, or
request-identity API route is added. The middleware does not read HTTP headers,
cookies, query parameters, or request bodies. `X-AION-Actor-ID` remains request
metadata only and is ignored as production identity.

## AION-157 Runtime Guard Renewal

`runtime_guard_hold_active=true` and `runtime_no_go_status=true` remain in force
for AION-158. `runtime_implementation_approved=false`,
`production_auth_runtime_enabled=false`, `identity_verification_enabled=false`,
`authenticated_requests_enabled=false`,
`runtime_enablement_guard_release_approved=false`,
`runtime_enablement_guard_final_lock_release_approved=false`, and
`runtime_enablement_master_lock_release_approved=false`.

AION-157 does not approve header parsing, cookie parsing, credentials,
passwords, tokens, sessions, external providers, network clients, auth
endpoints, OpenAPI security schemes, SDK resources, CLI commands, packages,
lockfiles, migrations, v0.2 tags, or v0.2 releases.

AION-158 stabilizes only the disabled middleware mechanics. The pure ASGI
middleware still authenticates nobody, passes receive and send unchanged,
bypasses non-HTTP scopes, preserves streaming and request bodies, propagates
cancellation, clears state on disconnect, replaces forged identity state, and
prevents duplicate registration.

## AION-159 Runtime Hold

AION-159 keeps request identity runtime disabled and closes the consumed
AION-157 stabilization authorization. The actor-context trust-boundary
authorization for AION-160 does not enable identity verification,
authenticated requests, header parsing, cookie parsing, credentials, tokens,
sessions, providers, runtime routes, SDK/CLI resources, tags, or releases.
