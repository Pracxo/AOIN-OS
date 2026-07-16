# ADR 0149: v0.2 Production Auth Request Identity Stabilization

Status: Accepted

## Context

`AION-156` implemented a disabled request identity boundary under
`aion_brain.production_auth`. `AION-157-PA-0004` authorizes `AION-158` to
stabilize that boundary without enabling runtime authentication.

## Role comparison

`RequestContextMiddleware` owns request IDs, trace IDs, correlation IDs,
idempotency metadata, safe request metadata, API audit, API telemetry, request
performance sampling, and response correlation headers. It does not
authenticate users.

The request-identity boundary owns anonymous disabled identity evidence,
request-scoped disabled context, audit evidence, provenance evidence, status,
and diagnostics. `auth_runtime` remains a disabled preview surface.
`production_auth` owns the disabled internal implementation.

## AION-157 authorization

`AION-157-PA-0004` is the stabilization authorization for `AION-158`.
It is not reusable and expires on the AION-158 merge.

## Existing BaseHTTPMiddleware implementation

The prior middleware used Starlette `BaseHTTPMiddleware`, `Request`, and
`Response` dispatch mechanics.

## BaseHTTPMiddleware limitations

That shape can obscure ASGI receive/send passthrough, streaming behavior,
request-body preservation, cancellation propagation, and non-HTTP scope bypass.

## Pure ASGI decision

Replace the implementation with pure ASGI while preserving the public class
name `ProductionAuthRequestIdentityMiddleware`.

## Compatibility strategy

Existing callers keep the middleware class name. The boundary still accepts the
existing `RequestContext` call style, while the middleware path passes only
`request_id`, `trace_id`, and `correlation_id`.

## Middleware registration strategy

The app factory uses `register_production_auth_request_identity_middleware`.
When disabled, zero instances are registered. When enabled, exactly one
instance is registered. A second registration raises a fixed `RuntimeError`.

## Middleware execution order

The effective order remains `RequestContextMiddleware`, then
`ProductionAuthRequestIdentityMiddleware`, then route execution.

## HTTP state flow

For HTTP scopes, the middleware reads `scope["state"]`, requires
`aion_request_context`, builds disabled evidence from safe correlation fields,
attaches immutable evidence, and calls downstream exactly once.

## Non-HTTP bypass

Websocket, lifespan, and unknown non-HTTP scopes bypass identity logic, mutate
no state, and preserve receive/send identity.

## Streaming preservation

The middleware does not buffer responses. Response start, body chunks,
`more_body` flags, chunk count, chunk order, and background execution remain
downstream behavior.

## Request-body preservation

The middleware does not call or wrap `receive`, instantiate `Request`, or read a
body. Request-body event ordering and disconnect visibility remain downstream
behavior.

## Cancellation propagation

`asyncio.CancelledError` clears partial request-identity state and is re-raised.

## Client-disconnect behavior

Downstream client disconnects clear identity evidence, set
`downstream_client_disconnect`, preserve no authenticated state, and are
re-raised.

## Forged-state defence

Pre-populated request-identity evidence keys are removed before trusted
disabled evidence is attached. A boolean
`aion_request_identity_forged_state_replaced=true` records replacement without
including forged objects or exception text.

## Duplicate-registration guard

Duplicate registration is rejected by inspecting `app.user_middleware`, not
only app state.

## Request-state isolation

Identity evidence is request-scoped. Sequential, concurrent, failed, cancelled,
and forged-state requests do not reuse evidence objects or leak request IDs,
trace IDs, correlation IDs, metadata, or failure indicators.

## Reentrancy and concurrency

The boundary remains state-free for request data and uses injected deterministic
factories for repeatable tests.

## Evidence idempotency

Canonical SHA-256 fingerprints remain self-excluding and deterministic for
identical inputs. Safety-relevant field changes alter fingerprints.

## Diagnostic hardening

Diagnostics expose only disabled state, pure ASGI flags, no-go booleans, and
implementation/stabilization lineage. They do not expose request data, actors,
headers, cookies, credentials, tokens, provider payloads, or exception text.

## Runtime restrictions

Runtime authentication, identity verification, authenticated requests, runtime
guard release, connector runtime, operator writes, module activation, sandbox
execution, v0.2 tags, and v0.2 releases remain disabled or absent.

## Parsing restrictions

No Authorization header, cookie, query parameter, client/server field, or body
is parsed for identity.

## Protected-material restrictions

No credential, password, token, session, private key, authorization header,
provider payload, raw body, raw prompt, or hidden reasoning is stored in request
identity evidence.

## Provider restrictions

No OAuth, OIDC, SAML, provider SDK, network client, external call, login,
logout, callback, token, session, or credential endpoint is introduced.

## API, SDK, and CLI restrictions

No public auth router, OpenAPI security scheme, SDK runtime resource, CLI
runtime command, package file, lockfile, or migration is added.

## Alternatives considered

Keeping `BaseHTTPMiddleware` was rejected because the stabilization requires
direct ASGI passthrough proof. Adding a runtime auth endpoint was rejected as
outside authorization.

## Security impact

The change reduces middleware ambiguity and adds forged-state and duplicate
registration guards while preserving anonymous disabled identity.

## Performance impact

The middleware avoids response buffering and request-body reads. Performance
coverage is a smoke test, not a runtime throughput claim.

## Consequences

The disabled boundary is safer to compose with streaming and cancellation
paths. Formal lifecycle closeout for `AION-157-PA-0004` is deferred to
`AION-159` after AION-158 is merged.

## AION-157 authorization expiry condition

The authorization expires when AION-158 merges or if explicitly revoked before
merge.
