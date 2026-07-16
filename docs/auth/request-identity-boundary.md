# Disabled Production Auth Request Identity Boundary

Status: `implemented_disabled`

`AION-156` implements the request identity boundary authorized by
`AION-155-PA-0003`. The boundary lives under `aion_brain.production_auth`, not
under `aion_brain.auth_runtime`, and it does not replace
`RequestContextMiddleware`.

## Role Comparison

`RequestContextMiddleware` still owns `request_id`, `trace_id`,
`correlation_id`, safe request metadata, API audit, telemetry, and performance
sampling. It may carry legacy `actor_id` metadata, but that value is never
treated as production identity.

`aion_brain.auth_runtime` remains a disabled preview and compatibility surface.
It does not become the production-auth implementation.

`aion_brain.production_auth` owns the internal disabled production-auth core and
the new request identity boundary. The boundary consumes only the safe
correlation values from `RequestContext` and attaches anonymous disabled
evidence to request state.

## Boundary State

- `request_identity_boundary_implemented=true`
- `request_identity_boundary_state=implemented_disabled`
- `request_identity_boundary_default_enabled=false`
- `request_identity_boundary_mode=observe_only_disabled`
- `authorization_transaction_id=AION-155-PA-0003`
- `implementation_task=AION-156`
- `authorization_scope=disabled-request-identity-boundary`
- `authorization_consumed_by_task=AION-156`
- `authorization_reusable=false`

## Runtime State

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

The boundary adds no public route, no OpenAPI security scheme, no SDK resource,
and no CLI command.

## AION-157 Closeout and Stabilization Authorization

`AION-155-PA-0003` is now historical evidence: `authorization_active=false`,
`authorization_consumed=true`, `authorization_consumed_by_task=AION-156`,
`authorization_consumed_by_pr=66`,
`authorization_consumed_by_feature_commit=2fbeb77bdc33772c46a679cbfa0bdafe327abb42`,
`authorization_consumed_by_merge_commit=051f6f2e8b901863f8dc9cad405e5b5401db3695`,
`authorization_expired=true`, and `authorization_reusable=false`.

`AION-157-PA-0004` is active for AION-158
`disabled-request-identity-boundary-stabilization`. AION-158 may harden the
disabled boundary mechanics, but real identity verification and authenticated
requests remain out of scope.

## AION-158 Stabilization

AION-158 replaces the request identity middleware mechanics with pure ASGI while
preserving this disabled boundary. The public middleware class name remains
stable, `RequestContextMiddleware` remains the request-correlation owner, and
the identity boundary still consumes only `request_id`, `trace_id`, and
`correlation_id`.
