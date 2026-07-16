# v0.2 Production Auth Request Identity Stabilization No-Go

Status: `enforced`

Reject the AION-158 branch if any of the following occur:

- `AION-155-PA-0003` reactivates.
- A second active record appears.
- An unknown approved record appears.
- AION-157 scope widens beyond disabled request identity stabilization.
- The implementation task is not `AION-158`.
- `ProductionAuthRequestIdentityMiddleware` uses `BaseHTTPMiddleware`,
  constructs Starlette `Request` or `Response`, inspects headers, cookies,
  query strings, client/server data, or request bodies, wraps `receive` or
  `send`, buffers responses, or trusts actor metadata.
- Non-HTTP scopes mutate identity state.
- Streaming responses or request-body events are buffered or reordered.
- Cancellation is swallowed.
- Client disconnects preserve identity evidence.
- Forged identity state survives.
- Duplicate middleware registration is allowed.
- Runtime authentication, identity verification, authenticated requests,
  headers, cookies, credentials, passwords, tokens, sessions, protected
  material, providers, network calls, endpoints, OpenAPI security, package
  files, lockfiles, migrations, SDK or CLI runtime surfaces, connector runtime,
  operator writes, module activation, sandbox execution, v0.2 tags, or v0.2
  releases appear.

The no-go state is `runtime_no_go_status=true`.
