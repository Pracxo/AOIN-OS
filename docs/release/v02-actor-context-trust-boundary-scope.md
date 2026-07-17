# v0.2 Actor Context Trust Boundary Scope

Status: `authorized-for-AION-160`

## Boundary

Development identity simulation is not production actor-context resolution.
AION-160 may preserve explicit development simulation only when both are true:
`settings.env == "development"` and `settings.dev_auth_enabled == true`.

Outside that exact gate, AION-160 must ignore identity-bearing `X-AION`
headers and return a fail-closed anonymous `ActorContext`.

## Required Future Behavior

- `actor_id=null`
- `actor_type=null`
- `workspace_id=null`
- `roles=[]`
- `permissions=[]`
- `security_scope=[]`
- `dev_mode=false`

`RequestIdentityContext` takes precedence over development headers unless the
request is in explicit development simulation mode. In the current disabled
state it remains anonymous and unauthenticated.

`RequestContext` owns `trace_id` and `correlation_id`. Those values may be
projected safely. Actor headers must not override them when RequestContext
exists.

## Route Dependency Impact

Routes that consume `ActorContext` must resolve it through the hardened
fail-closed resolver or a compatible wrapper. Route paths and response
contracts must not change.

## Required AION-160 Evidence

- event intake route regression
- memory retrieval route regression
- Brain think route regression
- representative actor-context route regressions
- non-development header rejection tests
- privilege escalation regression tests
- request payload actor metadata non-authentication tests
- development simulation compatibility tests
- audit and provenance evidence when useful

## Prohibited Runtime Work

AION-160 must not implement production identity verification, authenticated
requests, credential or token handling, sessions, cookies, providers, external
calls, auth endpoints, OpenAPI security, packages, migrations, SDK/CLI
runtime resources, connector runtime, operator writes, module activation,
sandbox execution, v0.2 tags, or v0.2 releases.
