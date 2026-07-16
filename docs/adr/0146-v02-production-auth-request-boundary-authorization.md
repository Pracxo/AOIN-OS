# 0146: v0.2 Production Auth Request Identity Boundary Authorization

Status: `accepted`

## Context

AION-154 merged the stabilized internal disabled production-auth core. That
merge satisfied the expiry condition for `AION-153-PA-0002`, so AION-155 closes
the old stabilization authorization and creates the next single-use
authorization for the future request identity boundary.

## Role Comparison

- AION-151 authorized the initial disabled production-auth core as
  `AION-151-PA-0001`.
- AION-152 implemented the internal disabled production-auth core.
- AION-153 authorized production-auth core stabilization as
  `AION-153-PA-0002`.
- AION-154 stabilized the internal core while keeping runtime auth disabled.
- AION-155 closes `AION-153-PA-0002` and authorizes AION-156.
- AION-156 may implement only the disabled request identity boundary.

## AION-154 Closeout

PR 64 merged feature commit `f001632ed0566bcf7facfe8905a2781ff9fa6ce9` through
merge commit `85584ea1976fd6f2cb73a641464b3caf87481618`. The core remains
`implemented_disabled`, and production-auth runtime remains false.

## AION-153 Authorization Consumption

`AION-153-PA-0002` is approved historical evidence. It is now inactive,
consumed by AION-154, expired, and non-reusable. It must never become active
again.

## AION-155 Authorization Decision

Create `AION-155-PA-0003` as the single active production-auth authorization.
It authorizes future `AION-156` work under
`authorization_scope=disabled-request-identity-boundary`.

## Exact AION-156 Scope

AION-156 may add request identity contracts, a provider-agnostic verifier
interface, disabled verifier behavior, deterministic local test verifier
behavior, anonymous disabled context attachment, observe-only boundary
registration, audit/provenance correlation, read-only diagnostics, tests, docs,
and static-console evidence.

## Request-Boundary Architecture

The boundary is an internal request-state attachment point. It may correlate
request IDs, trace IDs, audit events, and provenance records. Its permitted
runtime result is disabled and unauthenticated with no runtime effect.

## Disabled Verifier Role

The disabled verifier must always return an unauthenticated, disabled,
no-runtime-effect result.

## Deterministic Test Verifier Role

The deterministic verifier may be used only by tests or an explicit
non-production harness. It must not become production identity verification.

## Observe-Only Disabled Middleware Role

Any middleware registration must be disabled by default and observe-only. It may
attach anonymous disabled identity context only.

## Runtime Restrictions

No identity verification, authenticated requests, login/logout/callback
endpoints, Authorization header parsing, cookie parsing, token parsing, token
issuance, token refresh, session creation, cookie issuance, or runtime guard
release is permitted.

## Protected-Material Restrictions

No credentials, passwords, tokens, cookies, sessions, private keys, raw identity
claims, raw prompts, or hidden reasoning may be stored or emitted.

## Provider Restrictions

No external identity provider, OAuth runtime, OIDC runtime, SAML runtime,
network client, external call, or provider SDK is permitted.

## Release Restrictions

No package files, lockfiles, migrations, runtime API routes, SDK runtime
resources, CLI runtime commands, connector runtime, operator writes, module
activation, sandbox execution, v0.2 tag, or v0.2 release are permitted.

## Alternatives Considered

1. Reuse `AION-153-PA-0002`. Rejected because AION-154 consumed that
   single-use authorization.
2. Authorize full production authentication. Rejected because request identity
   and protected-material lifecycles are not ready.
3. Delay all request-boundary work. Rejected because a disabled observe-only
   boundary is the next safe integration step.

## Security Impact

The decision narrows future work to disabled request-state evidence and keeps
all authentication, protected-material, provider, and release gates locked.

## Expiry

`AION-155-PA-0003` expires when AION-156 merges or when it is explicitly
revoked.

## Revocation

Revocation requires a follow-up approval record referencing
`AION-155-PA-0003` and leaving runtime guards locked.

## Consequences

- `AION-153-PA-0002` is consumed, inactive, expired, and non-reusable.
- `AION-155-PA-0003` is created.
- AION-156 request-identity boundary implementation is authorized.
- Observe-only disabled request-state integration is permitted.
- Identity verification is not permitted.
- Authenticated requests are not permitted.
- Protected-material handling is not permitted.
- Provider integration is not permitted.
- Production-auth runtime remains disabled.
- Runtime no-go remains true.
- No v0.2 tag or release is created.
