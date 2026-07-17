# v0.2 Offline Identity Assertion Verification Scope

Task: AION-161

## Authorized AION-162 Scope

1. Strict signed-assertion contracts.
2. Fixed Ed25519 verifier.
3. Public-key-only trust registry.
4. Deterministic canonical payload serialization.
5. Signature domain separation.
6. Base64url decoding with strict validation.
7. Exact issuer validation.
8. Exact audience validation.
9. `issued_at`, `not_before`, and `expires_at` validation.
10. Maximum assertion lifetime enforcement.
11. Clock-skew enforcement.
12. Assertion ID validation.
13. Claim shape and size constraints.
14. Multiple public keys selected by exact key ID.
15. Key activation, retirement, and revocation state.
16. Fail-closed unknown-key behavior.
17. Fail-closed signature behavior.
18. Audit and provenance evidence.
19. Deterministic test fixtures.
20. Test-only ephemeral signing keys.
21. Negative cryptographic regression tests.
22. Dependency-free canonicalization reuse.
23. Documentation and read-only static-console evidence.

## Authorized Source Paths

- `services/brain-api/src/aion_brain/contracts/identity_assertion.py`
- `services/brain-api/src/aion_brain/production_auth/identity_assertion.py`
- `services/brain-api/src/aion_brain/production_auth/identity_assertion_verifier.py`
- `services/brain-api/src/aion_brain/production_auth/trusted_public_keys.py`
- `services/brain-api/src/aion_brain/production_auth/identity_assertion_evidence.py`
- `services/brain-api/src/aion_brain/production_auth/__init__.py`
- `services/brain-api/pyproject.toml`
- `services/brain-api/tests/`
- `docs/`
- `examples/`
- `operator-console-static/`
- `scripts/`

KernelContainer and diagnostics may change only if AION-162 adds an inert, disabled, empty-registry verification service with zero request integration.

## Explicit Prohibitions

AION-162 must not parse HTTP headers, Authorization, Cookie, or request bodies; register middleware; replace `DisabledRequestIdentityVerifier`; populate RequestIdentityContext; populate ActorContext; authenticate a request; authorize a route; add a route or API router; add OpenAPI security; load runtime signing material; persist or serialize signing material; ship a signing service; log raw assertions; persist verified claims; contact providers; fetch JWKS; perform provider discovery; perform network calls; implement OAuth, OIDC, or SAML; issue or refresh tokens; store tokens; create or persist sessions; issue or persist cookies; add a replay cache; add migrations; add package manifests or lockfiles; add SDK or CLI runtime surfaces; enable connector runtime, operator writes, module activation, or sandbox execution; release runtime guards; or create a v0.2 tag or release.
