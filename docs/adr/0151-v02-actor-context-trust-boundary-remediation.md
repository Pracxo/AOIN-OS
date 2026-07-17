# 0151: v0.2 Actor Context Trust Boundary Remediation

## Status

Accepted for AION-160 implementation.

## Context

AION-159 authorized remediation of a non-development actor-context trust
boundary defect under `AION-159-PA-0005`. The existing development identity
helper could project caller supplied identity-bearing `X-AION` headers into
route `ActorContext` outside explicit development simulation.

## Decision

Introduce `ProductionAuthActorContextResolver` as the internal fail-closed
actor-context resolver. Keep `get_actor_context` and
`actor_context_from_headers` compatible for existing route dependencies.

Development identity headers are read only when:

```python
settings.env == "development" and settings.dev_auth_enabled is True
```

Outside that exact gate, identity-bearing `X-AION` headers are ignored. A valid
disabled `RequestIdentityContext` has precedence as identity evidence, but it
does not authenticate the request or populate the actor. Only `trace_id` and
`correlation_id` may project from `RequestContext`; request actor and workspace
metadata are ignored.

The fail-closed result outside development simulation is anonymous and
zero-permission. Request payload actor data may remain domain attribution
metadata where existing contracts permit it, but it is not authentication and
does not grant permissions or scope.

## Role Comparison

`RequestContextMiddleware` owns request IDs, trace and correlation propagation,
idempotency metadata, safe API metadata, request audit lifecycle, telemetry,
performance sampling, and response correlation headers.

`RequestIdentityContext` owns disabled identity evidence:
`authentication_state=disabled`, `authenticated=false`, `actor_id=null`,
`subject=null`, `roles=[]`, and `runtime_effect=false`.

`ActorContext` owns route actor, workspace, roles, permissions, security scope,
trace, correlation, and development-mode marker.

`identity/dev_auth.py` owns explicit local development simulation only.

## Evidence Model

AION-160 adds strict frozen Pydantic contracts for resolution status, audit
events, provenance records, diagnostic snapshots, and bundles. Evidence uses
the production-auth canonical SHA-256 fingerprinting helper and stores no raw
headers, cookies, tokens, credentials, provider payloads, request bodies, raw
prompts, hidden reasoning, or forged object representations.

## Security Impact

Hostile non-development actor, workspace, role, permission, and security-scope
headers no longer grant route identity, permissions, or scope. Wrong-type
request identity state fails closed. Concurrent requests do not share actor,
role, permission, security-scope, request identity, audit, provenance, trace, or
correlation state.

## Runtime Restrictions

AION-160 adds no production identity verification, authenticated requests,
Authorization parsing, Cookie parsing, credentials, passwords, tokens,
sessions, external providers, network clients, auth API routers, OpenAPI
security, package files, lockfiles, migrations, SDK runtime resources, CLI
runtime commands, connector runtime, operator writes, module activation,
sandbox execution, runtime guard release, `v0.2` tag, or `v0.2` release.

## Alternatives Considered

Editing every route was rejected because it would increase route drift and
miss compatibility callers. Treating `RequestContext.actor_id` as verified
identity was rejected because that field is still untrusted request metadata.
Making `RequestIdentityContext` authenticated was rejected because production
authentication remains disabled.

## Consequences

Route imports remain stable. Development simulation remains available for local
work. Non-development actor context is fail-closed until a separately
authorized production identity verification path exists.

The AION-160 merge satisfies the `AION-159-PA-0005` expiry condition. Formal
authorization lifecycle closeout belongs to AION-161.
