# v0.2 Actor Context Trust Boundary Runtime Hold

AION-160 keeps the production-auth runtime guard closed while remediating the
actor-context trust boundary.

Required runtime state:

- `actor_context_trust_boundary_remediated=true`
- `actor_context_resolution_state=implemented_fail_closed`
- `runtime_guard_hold_active=true`
- `runtime_no_go_status=true`
- `runtime_implementation_approved=false`
- `production_auth_runtime_enabled=false`
- `identity_verification_enabled=false`
- `authenticated_requests_enabled=false`
- `authenticated_actor_context_enabled=false`
- `non_development_identity_headers_ignored=true`
- production actor, workspace, role, permission, and security-scope header trust false
- Authorization and Cookie parsing false
- credential, password, token, and session handling false
- provider, network, endpoint, package, lockfile, migration, SDK, CLI, connector, operator, module, sandbox, tag, and release state false

Validation:

- `./scripts/production-auth-actor-context-trust-boundary-check.sh`
- `./scripts/production-auth-actor-context-trust-boundary-runtime-hold.sh`
- `./scripts/production-auth-actor-context-trust-boundary-no-go-regression.sh`
