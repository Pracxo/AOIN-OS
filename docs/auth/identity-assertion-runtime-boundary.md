# Identity Assertion Runtime Boundary

AION-162 keeps offline assertion verification separated from request
authentication.

Required disabled states:

- `request_authenticated=false`
- `actor_context_applied=false`
- `request_identity_context_applied=false`
- `runtime_effect=false`
- `runtime_integration_allowed=false`
- `identity_assertion_header_parsing_enabled=false`
- `authorization_header_parsing_enabled=false`
- `cookie_parsing_enabled=false`
- `identity_assertion_middleware_registered=false`
- `external_calls_enabled=false`
- `jwks_network_fetch_enabled=false`
- `provider_discovery_enabled=false`
- `runtime_api_routes_added=false`
- `openapi_security_scheme_added=false`
- `sdk_runtime_resource_added=false`
- `cli_runtime_command_added=false`
- `lockfiles_added=false`
- `migrations_added=false`
- `v02_tag_created=false`
- `v02_release_created=false`

The boundary is enforced by focused tests and
`scripts/production-auth-offline-identity-assertion-runtime-hold.sh`.


## AION-163 Replay Protection Authorization Update

AION-163 records AION-162 PR #72 and corrective PR #73 as the completed offline verification delivery, closes `AION-161-PA-0006` as inactive, consumed, expired, and non-reusable, and creates `AION-163-PA-0007` as the sole active authorization for AION-164 persistent identity-assertion replay protection. The next critical path is AION-164. Runtime request authentication, ActorContext application, RequestIdentityContext application, dependency changes, migrations, production schema auto-create, package files, lockfiles, v0.2 tags, and v0.2 releases remain blocked.
