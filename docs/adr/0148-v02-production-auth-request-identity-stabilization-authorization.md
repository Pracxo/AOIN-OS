# ADR 0148: v0.2 Production Auth Request Identity Stabilization Authorization

Status: Accepted

## Context

AION-156 implemented the disabled request identity boundary under
`AION-155-PA-0003` and merged as PR 66. The implementation added strict
contracts, provider-agnostic disabled verifiers, anonymous disabled request
state, observe-only middleware, audit and provenance correlation, diagnostics,
tests, and read-only evidence. Production authentication runtime remains
disabled and no public auth route exists.

## Decision

AION-157 marks `AION-155-PA-0003` consumed, inactive, expired, and
non-reusable. It creates `AION-157-PA-0004` as the AION-158 authorization
for AION-158 request identity boundary stabilization.

AION-158 may migrate the middleware implementation to pure ASGI if that removes
BaseHTTPMiddleware risks around streaming, cancellation, scope handling, and
receive/send invariants. It must preserve RequestContextMiddleware ownership,
anonymous disabled identity, provider-agnostic disabled verifier behavior,
middleware ordering, streaming responses, request bodies, non-HTTP scope bypass,
request-state integrity, concurrency and reentrancy safety, evidence
idempotency, diagnostics, and performance-smoke coverage.

## Restrictions

AION-157 and the future AION-158 scope do not approve identity verification,
authenticated requests, header parsing, cookie parsing, credential or password
handling, token handling, session handling, external providers, external calls,
auth endpoints, OpenAPI security, package files, lockfiles, migrations, SDK or
CLI runtime surfaces, connector runtime, operator writes, module activation,
sandbox execution, runtime guard release, v0.2 tags, or v0.2 releases.

## Alternatives Considered

- Keep the BaseHTTPMiddleware implementation unchanged. Rejected for AION-158
  stabilization because pure ASGI gives clearer streaming and cancellation
  invariants.
- Broaden AION-158 into runtime authentication. Rejected because no runtime
  guard release exists.

## Consequences

The next task may harden the disabled request identity boundary mechanics, but
it cannot authenticate users or parse protected material. `AION-157-PA-0004`
expires when AION-158 merges or when it is explicitly revoked.
