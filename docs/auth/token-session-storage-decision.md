# Token And Session Storage Decision

## Decision

AION-098 does not implement token storage, session storage, cookies, login
routes, logout routes, provider SDKs, or credential storage. The design
decision is to keep future token handling inside a dedicated production auth
boundary and to require a separate release gate before any runtime storage
is added. AION-099 does not change this decision; the disabled auth runtime
prototype reports token issuance, cookie issuance, and session persistence as
disabled.
exists.

## Token Handling Rules

- validate tokens only in the future auth boundary
- never expose token values through Brain public contracts
- never log token values
- never store token values in examples, telemetry, audit, or docs
- never use token claims directly as permissions without AION role mapping and
  policy authorization

## Session Handling Rules

- future sessions must be short-lived, scoped, revocable, and auditable
- browser state is not authoritative
- session identifiers must not appear in docs or examples
- session creation must pass release gates before runtime code exists
- logout and timeout behavior must be tested before enablement

## Storage Options

| Option | Status | Notes |
| --- | --- | --- |
| Server-side session store | future candidate | requires encryption, rotation, expiry, revocation, audit |
| Signed secure cookie | future candidate | requires CSRF, SameSite, secure flag, rotation, revocation strategy |
| Stateless token only | not preferred | weak server-side revocation unless paired with provider/introspection controls |
| Browser localStorage | forbidden | protected material must not be stored in localStorage |

## Forbidden Storage

- plaintext credentials
- provider secrets in repo or examples
- token values in logs, telemetry, docs, or examples
- browser localStorage auth material
- session rows before approved migration
- cookie issuance before CSRF/CORS review

## Local Dev Constraints

Local auth remains synthetic and dev-only. AION-099 may use mock-only claims
behind disabled runtime flags. It must not call a real provider or issue real
tokens.

## Production Constraints

Production auth requires provider selection, threat model approval, token and
session storage approval, CSRF/CORS design approval, role mapping approval,
audit correlation tests, revocation tests, security review, and rollback plan.

## Revocation Model

Future auth must define provider revocation, local session revocation, stale
role mapping handling, and audit evidence for revocation events before runtime
enablement.

## Timeout Model

Future sessions must define idle timeout, absolute timeout, refresh behavior,
logout behavior, and operator-visible expiry state before runtime enablement.

## No Implementation Yet

No token parser, token issuer, session table, cookie writer, provider SDK, or
login/logout endpoint is added in AION-098.
