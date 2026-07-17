# Actor Context Trust Boundary

AION-160 implements the actor-context trust-boundary remediation authorized by
`AION-159-PA-0005`.

## Current Defect

Before AION-160, the development identity helper could project caller supplied
`X-AION` identity headers into `ActorContext` even when the request was not in
the exact development simulation mode. The affected headers were:

- `X-AION-Actor-ID`
- `X-AION-Workspace-ID`
- `X-AION-Roles`
- `X-AION-Permissions`
- `X-AION-Security-Scope`

Those headers are not a production identity source. They are untrusted outside
the explicit development simulation gate.

## Remediation

`ProductionAuthActorContextResolver` resolves route actor context from
structured safe primitives only. It never receives a raw HTTP request, headers,
cookies, query parameters, request bodies, raw ASGI scope, credentials, tokens,
provider payloads, or sessions.

Outside explicit development simulation the resolver returns an anonymous
zero-permission `ActorContext`:

- `actor_id=null`
- `actor_type=null`
- `workspace_id=null`
- `roles=[]`
- `permissions=[]`
- `security_scope=[]`
- `dev_mode=false`

Only `trace_id` and `correlation_id` may be projected from `RequestContext` to
`ActorContext`. `request_id` is used only for evidence correlation. The
`RequestContext.actor_id`, `RequestContext.workspace_id`, idempotency key,
method, path, and metadata remain untrusted request metadata and are ignored by
actor-context resolution.

## Request Identity Precedence

When a valid disabled `RequestIdentityContext` exists outside development
simulation, it is treated as the primary identity-evidence source. Because the
request identity boundary is still disabled, the resulting actor context remains
anonymous with zero roles, zero permissions, and zero security scope.

Wrong-type or invariant-violating request identity objects fail closed without
storing the forged object representation.

## Runtime Hold

AION-160 does not enable production authentication. These states remain false:

- identity verification
- authenticated requests
- authenticated actor context
- Authorization or Cookie parsing
- credentials, passwords, tokens, sessions, providers, and external calls
- production-auth API routes and OpenAPI security
- package files, lockfiles, migrations, SDK runtime resources, and CLI runtime commands
- connector runtime, operator writes, module activation, sandbox execution
- `v0.2` tag or release

Formal lifecycle closeout for `AION-159-PA-0005` is recorded by AION-161.
`AION-159-PA-0005` is inactive, consumed by AION-160 PR 70, expired, and
non-reusable. `AION-161-PA-0006` is the active follow-up authorization for
AION-162 offline Ed25519 identity assertion verification; it does not approve
request authentication or ActorContext application.
## AION-162 Interaction

AION-162 does not change ActorContext resolution. Offline identity assertion
verification returns redacted evidence only and always records
`actor_context_applied=false`. Fail-closed ActorContext behavior from AION-160
remains the active boundary until a separate request-integration authorization.
