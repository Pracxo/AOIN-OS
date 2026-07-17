# v0.2 Actor Context Trust Boundary Remediation

Status: implemented fail closed

Authorization transaction: `AION-159-PA-0005`

Implementation task: `AION-160`

Scope: `fail-closed-actor-context-resolution`

## Pre-Change Evidence

AION-159 documented a non-development identity-header trust fallback in
`aion_brain.identity.dev_auth`. The fallback allowed caller supplied `X-AION`
identity headers to populate route `ActorContext` when the request was not in
explicit development simulation. AION-160 remediates that behavior.

No live headers, credentials, tokens, cookies, sessions, provider payloads, or
user data are included in this evidence.

## Implementation

AION-160 introduces `ProductionAuthActorContextResolver` and the
`ActorContextResolution*` evidence contracts. The resolver accepts immutable
structured input rather than a raw HTTP request.

Route compatibility is preserved through `get_actor_context` and
`actor_context_from_headers`. The compatibility wrapper may parse identity
headers only when `development_identity_simulation_enabled(settings)` returns
true.

Outside the exact development gate, identity-bearing headers are ignored and
the returned `ActorContext` is anonymous, zero-permission, and zero-scope.

## Route Audit

| Route module | Dependency | Actor use | Workspace use | Role use | Permission use | Scope use | AION-160 regression |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `api/events.py` | `get_actor_context` | fills event actor metadata only when payload omits it | fills event workspace only when payload omits it | none | none | event security scope | `test_actor_context_route_integration.py` |
| `api/memory.py` | `get_actor_context` | retrieval filters | none | none | none | request scope fallback | `test_actor_context_route_integration.py` |
| `api/brain.py` | `get_actor_context` | brain-loop event metadata | workspace event metadata | none | permission context | security scope | `test_actor_context_route_integration.py` |
| `api/operator_actions.py` | `get_actor_context` | operator preview attribution | workspace attribution | role-aware preview evidence | action authorization preview | security scope evidence | `test_actor_context_privilege_escalation.py` |

Route paths and public request/response contracts remain unchanged.

## Runtime Hold

Production authentication remains disabled. No runtime authentication endpoints,
OpenAPI security schemes, provider integrations, credentials, tokens, sessions,
package files, lockfiles, migrations, SDK runtime resources, CLI runtime
commands, connector runtime, operator writes, module activation, sandbox
execution, `v0.2` tag, or `v0.2` release are added.

## Lifecycle

`AION-159-PA-0005` is consumed by AION-160 when this remediation merges. Formal
authorization lifecycle closeout is deferred to AION-161.
