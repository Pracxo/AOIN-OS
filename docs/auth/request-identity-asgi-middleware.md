# Request Identity ASGI Middleware

Status: `pure_asgi`

`ProductionAuthRequestIdentityMiddleware` is a pure ASGI middleware that
preserves the public class name from `AION-156` while removing
`BaseHTTPMiddleware`.

## Execution

For HTTP scopes, the middleware reads only `scope["state"]` and requires
`state["aion_request_context"]` to be a `RequestContext`. It passes only
`request_id`, `trace_id`, and `correlation_id` into the disabled boundary.

For non-HTTP scopes, including websocket, lifespan, and unknown future scope
types, it mutates no state and calls the downstream ASGI app exactly once with
the original `receive` and `send` callables.

## State Keys

The middleware owns only these request identity state keys:

- `aion_request_identity_context`
- `aion_request_identity_verification`
- `aion_request_identity_audit_event`
- `aion_request_identity_provenance`
- `aion_request_identity_boundary_bundle`
- `aion_request_identity_boundary_failed`
- `aion_request_identity_boundary_failure_reason`
- `aion_request_identity_boundary_attached`

Pre-populated identity evidence is treated as forged state, removed, and
replaced with fresh anonymous disabled evidence. The safe indicator is
`aion_request_identity_forged_state_replaced=true`.

## Failure Semantics

`asyncio.CancelledError` clears partial identity state and is re-raised.
Downstream client disconnects clear identity evidence, set
`downstream_client_disconnect`, and are re-raised. Boundary construction errors
clear partial identity state, set `boundary_construction_failed_closed`, and
continue unauthenticated.

## Preservation

The middleware does not instantiate a Starlette `Request` or `Response`, does
not inspect headers, cookies, query strings, client/server data, or request
bodies, and does not call or wrap `receive` or `send`. Streaming response
events, request-body events, `more_body` flags, and background execution remain
owned by the downstream application.
