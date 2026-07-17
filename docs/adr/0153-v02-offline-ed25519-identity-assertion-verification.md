# 0153: v0.2 Offline Ed25519 Identity Assertion Verification

## Context

AION-161 created `AION-161-PA-0006` to authorize AION-162 to implement an
offline identity assertion verification core. Prior production-auth work kept
request authentication disabled and hardened request and ActorContext
boundaries.

## Decision

Implement only offline Ed25519 verification. Use exactly
`cryptography>=49.0.0,<50.0.0`. Use no algorithm negotiation, no HMAC, no JWT,
no OIDC, no SAML, no JWKS discovery, and no provider networking.

The assertion uses a strict envelope, strict payload, domain-separated canonical
JSON, strict unpadded base64url, exact key-ID selection, public verification
keys only, key activation and retirement windows, key revocation, issuer
validation, audience validation, UTC temporal validation, and claim
constraints.

Verification produces safe audit, provenance, diagnostic, and result evidence.
Evidence is redacted, fingerprinted, and contains claim counts rather than raw
claims. Cryptographic verification is not request authentication.

Replay protection remains absent and is required before request integration.
Request authentication remains disabled. ActorContext application remains
disabled. RequestIdentityContext application remains disabled. Runtime private
signing keys are absent; test signing keys are ephemeral and in memory only.

No API route, OpenAPI security scheme, SDK runtime surface, CLI runtime surface,
provider network path, package manifest, lockfile, migration, v0.2 tag, or v0.2
release is created.

## Consequences

AION OS gains deterministic offline cryptographic verification primitives and
regression coverage while keeping the production-auth runtime guard locked.
Operational public-key provisioning, replay protection, request-level
integration, external provider integration, credential lifecycle, token
lifecycle, session lifecycle, and formal authorization closeout remain future
work. The AION-161 authorization expires when AION-162 is merged; formal
lifecycle closeout is deferred to AION-163.
