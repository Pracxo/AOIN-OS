# Request Identity Stabilization

Status: `implemented_disabled`

`AION-158` stabilizes the disabled production-auth request identity boundary
authorized by `AION-157-PA-0004`. The stabilization keeps the original
implementation lineage from `AION-155-PA-0003` and `AION-156` while replacing
the middleware mechanics with a pure ASGI implementation.

## Lineage

- `implementation_authorization_transaction_id=AION-155-PA-0003`
- `implementation_authorization_task=AION-156`
- `implementation_authorization_scope=disabled-request-identity-boundary`
- `stabilization_authorization_transaction_id=AION-157-PA-0004`
- `stabilization_authorization_task=AION-158`
- `stabilization_authorization_scope=disabled-request-identity-boundary-stabilization`
- `stabilization_authorization_reusable=false`
- `stabilization_authorization_expires_on_aion_158_merge=true`

## Stabilized State

- `request_identity_boundary_implemented=true`
- `request_identity_boundary_state=implemented_disabled`
- `request_identity_boundary_default_enabled=false`
- `request_identity_boundary_mode=observe_only_disabled`
- `request_identity_middleware_implementation=pure_asgi`
- `streaming_passthrough=true`
- `request_body_passthrough=true`
- `cancellation_propagation=true`
- `non_http_scope_bypass=true`
- `duplicate_registration_prevented=true`

## Runtime Hold

The boundary still authenticates nobody:

- `authentication_state=disabled`
- `authenticated=false`
- `actor_id=null`
- `subject=null`
- `roles=[]`
- `runtime_effect=false`
- `identity_verification_enabled=false`
- `authenticated_requests_enabled=false`
- `production_auth_runtime_enabled=false`
- `runtime_no_go_status=true`

No Authorization header, cookie, query parameter, request body, credential,
password, token, session, provider, network client, route, OpenAPI security
scheme, package, lockfile, migration, SDK runtime resource, CLI runtime command,
connector runtime, operator write, module activation, sandbox execution, v0.2
tag, or v0.2 release is introduced.

## AION-159 Closeout

AION-158 stabilization is merged and `AION-157-PA-0004` is consumed, expired,
inactive, and non-reusable. AION-159 adds no request identity implementation
source changes. It creates the next single-use authorization,
`AION-159-PA-0005`, for fail-closed actor-context trust-boundary remediation
in AION-160.
