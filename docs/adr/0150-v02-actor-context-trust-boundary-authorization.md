# ADR 0150: v0.2 Actor Context Trust Boundary Remediation Authorization

Status: accepted

## Context

AION-158 merged the disabled request identity stabilization with pure ASGI
middleware while keeping production authentication disabled. AION-159 closes
`AION-157-PA-0004` as consumed and authorizes AION-160 to remediate an
actor-context trust-boundary gap.

`RequestContextMiddleware` owns request IDs, trace IDs, correlation IDs,
idempotency metadata, API audit lifecycle, telemetry, and performance
sampling. It is not an authentication mechanism.

`RequestIdentityContext` represents request-scoped identity evidence. It is
currently anonymous, disabled, never trusts actor headers, never parses
Authorization headers, never parses cookies, never verifies credentials or
tokens, and has zero runtime effect.

`ActorContext` is consumed by Brain routes and carries actor ID, workspace ID,
roles, permissions, and security scope. It influences event, memory, planning,
and Brain-loop metadata.

`identity/dev_auth.py` is a development identity simulation layer. It may read
`X-AION` development headers only under an explicit development gate. It must
never act as a production identity source.

## Finding

The current non-development branch of `actor_context_from_headers` reads
identity-bearing `X-AION` headers when development authentication is disabled.
This is documented as a non-development identity-header trust fallback.
Unverified caller-controlled identity metadata can be projected into
`ActorContext` when development authentication is disabled.

## Decision

- Mark `AION-157-PA-0004` consumed, inactive, expired, and non-reusable.
- Create `AION-159-PA-0005`.
- Authorize AION-160 actor-context trust-boundary remediation.
- Accept `X-AION` identity headers only in explicit development simulation.
- Ignore identity-bearing `X-AION` headers outside explicit development mode.
- Use `RequestIdentityContext` as the primary identity-evidence source.
- Use `RequestContext` as the safe trace and correlation source.
- Return anonymous zero-permission `ActorContext` outside development simulation.
- Permit no real identity verification.
- Permit no authenticated requests.
- Keep runtime no-go true.
- Create no v0.2 tag or release.

## AION-160 Scope

AION-160 may introduce a fail-closed resolver, preserve development simulation
only when `settings.env == "development"` and
`settings.dev_auth_enabled == true`, harden route dependencies, and add
privilege-escalation, request-identity precedence, correlation, audit,
provenance, and compatibility regression tests.

## Restrictions

AION-160 must not add runtime authentication, Authorization or Cookie parsing,
protected-material handling, providers, external calls, auth endpoints,
OpenAPI security, package files, lockfiles, migrations, SDK or CLI runtime
surfaces, connector runtime, operator writes, module activation, sandbox
execution, v0.2 tags, or v0.2 releases.

## Alternatives Considered

Leaving the current fallback untouched would preserve caller-controlled
identity projection outside development mode. Enabling real production
authentication now would exceed the approved disabled-runtime boundary.

## Consequences

The actor-context remediation becomes the next release blocker. AION-159 adds
governance, evidence, tests, and gates only. Runtime remains disabled until a
future authorization explicitly changes the guard state.

## Expiry and Revocation

`AION-159-PA-0005` expires when AION-160 merges or when explicitly revoked.
Revocation must preserve runtime holds and must not reactivate historical
authorizations.
