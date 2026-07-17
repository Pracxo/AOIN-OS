# 0152: v0.2 Offline Ed25519 Identity Assertion Verification Authorization

## Status

Accepted for AION-161.

## Context

AION-160 merged the fail-closed actor-context trust-boundary remediation. The actor-context resolver now ignores non-development identity headers, keeps development simulation isolated, applies disabled RequestIdentityContext precedence, and returns anonymous zero-permission ActorContext outside development simulation.

`AION-159-PA-0005` is therefore consumed by AION-160 PR 70, feature commit `085b1b9d9cbbc23a735c1a82be66a2e901a56761`, and merge commit `bfc2afdc96358559027ee36efc0bc26ed3bb796d`. It is inactive, consumed, expired, and non-reusable.

## Role Comparison

`ProductionAuthActorContextResolver` performs fail-closed ActorContext resolution and no cryptographic verification.

`RequestIdentityVerifier` remains disabled, provider-agnostic, correlation-only, and authenticates nobody.

AION-161 authorizes AION-162 to add an offline verification core only. Verification output is not request authentication and must not apply ActorContext or RequestIdentityContext.

## Alternatives

HMAC/shared-secret verification was rejected because it requires shared-secret distribution, rotation, and protected-material lifecycle support that does not exist yet.

JWT/OIDC/JWKS integration was deferred because it combines HTTP parsing, algorithm selection, key discovery, provider trust, token semantics, and runtime request authentication.

## Decision

Create `AION-161-PA-0006` as the sole active authorization for AION-162 offline Ed25519 identity assertion verification.

Approve exactly `cryptography>=49.0.0,<50.0.0` as a future AION-162 change to `services/brain-api/pyproject.toml`.

Use public verification keys only. Runtime private keys, private-key configuration, private-key persistence, and private-key serialization remain prohibited.

Use a fixed Ed25519 algorithm, no algorithm negotiation, domain-separated signature input, and canonical JSON reuse.

Require strict assertion contracts, a public-key registry, key rotation semantics, issuer validation, audience validation, temporal validation, claim constraints, audit and provenance evidence, deterministic negative tests, and test-only in-memory signing keys.

Keep HTTP parsing, request authentication, ActorContext integration, RequestIdentityContext integration, provider networking, replay protection runtime, API routes, SDK/CLI runtime surfaces, connector runtime, operator writes, module activation, sandbox execution, v0.2 tags, and v0.2 releases prohibited.

## Consequences

AION-162 can implement an offline cryptographic verification core with public-key-only trust and deterministic fail-closed tests.

Runtime authentication remains disabled. Replay protection is unimplemented and required before request integration. External provider integration and protected-material handling beyond public verification keys remain blockers.

No AION-161 implementation source, package manifest, migration, runtime route, v0.2 tag, or v0.2 release is created.
