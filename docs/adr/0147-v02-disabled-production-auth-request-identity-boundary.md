# 0147: v0.2 Disabled Production Auth Request Identity Boundary

Status: accepted

## Context

`AION-155-PA-0003` authorized one scoped implementation task:
`AION-156`, the disabled request identity boundary. The authorization permits
an internal observe-only boundary and evidence model, but does not permit
runtime authentication.

## Role Comparison

`RequestContextMiddleware` owns request correlation, safe request metadata, API
audit, telemetry, and performance sampling. `aion_brain.auth_runtime` remains a
disabled preview and compatibility package. `aion_brain.production_auth` owns
the internal disabled production-auth core and the new request identity
boundary.

## Decision

Implement a separate internal request identity boundary under
`aion_brain.production_auth`. The boundary consumes only `request_id`,
`trace_id`, and `correlation_id` from `RequestContext`. It never trusts
`RequestContext.actor_id` or `X-AION-Actor-ID` as production identity.

## Middleware Order

The app factory registers `ProductionAuthRequestIdentityMiddleware` before
`RequestContextMiddleware` so Starlette wrapping makes `RequestContextMiddleware`
execute first. Integration tests prove the identity middleware receives
`request.state.aion_request_context`.

## Verifier Decision

Use a provider-agnostic `RequestIdentityVerifier` protocol. The production
container constructs only `DisabledRequestIdentityVerifier`. Tests may use
`DeterministicDisabledTestVerifier`; it still returns disabled anonymous
results.

## Anonymous Context

All identity evidence remains:

- `authentication_state=disabled`
- `authenticated=false`
- `actor_id=null`
- `subject=null`
- `roles=[]`
- `runtime_effect=false`

## Audit And Provenance

The boundary emits redacted audit and provenance evidence correlated to the
authorization transaction, implementation task, request ID, trace ID when
present, correlation ID when present, boundary version, and verifier type.

## Configuration Default

`production_auth_request_boundary_enabled=false` and
`AION_PRODUCTION_AUTH_REQUEST_BOUNDARY_ENABLED=false`.

## Runtime Boundary

The boundary performs no identity verification, no authenticated request
enablement, no Authorization header parsing, no Cookie parsing, no protected
material handling, no provider integration, no external call, no API route, no
SDK runtime resource, no CLI command, no migration, no package addition, no
v0.2 tag, and no v0.2 release.

## Alternatives Considered

Merging the boundary into `auth_runtime` was rejected because `auth_runtime`
remains a disabled preview surface. Replacing `RequestContextMiddleware` was
rejected because request correlation and API audit are already owned there.
Trusting actor metadata was rejected because legacy request metadata is not
production identity.

## Security Impact

The implementation creates an immutable anonymous disabled context only. It
adds no credential, token, cookie, provider, or authenticated authorization
path. Missing request context fails closed by marking request state and
continuing unauthenticated where safe.

## Consequences

`AION-155-PA-0003` is consumed by `AION-156` and is non-reusable. The
authorization expiry condition is satisfied when the AION-156 merge lands.
Future real identity verification, provider integration, protected-material
lifecycle, and runtime guard release require separate authorization.
