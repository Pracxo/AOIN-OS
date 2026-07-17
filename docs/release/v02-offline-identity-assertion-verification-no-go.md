# v0.2 Offline Identity Assertion Verification No-Go

Task: AION-161

The AION-161 no-go state fails if any of the following occurs:

- more than one active approved authorization exists
- `AION-159-PA-0005` reactivates
- `AION-161-PA-0006` is missing, consumed, expired, reusable, or scoped incorrectly
- a cryptographic implementation permission is missing
- an extra approved permission is present
- the dependency is anything other than `cryptography>=49.0.0,<50.0.0`
- more than one dependency change is approved
- AION-161 changes implementation source or `services/brain-api/pyproject.toml`
- HTTP header parsing, Authorization parsing, Cookie parsing, request authentication, ActorContext application, or RequestIdentityContext application is approved
- runtime private-key material, private-key configuration, persistence, or serialization is approved
- raw assertion logging or verified-claims persistence is approved
- provider discovery, JWKS fetch, external calls, provider SDKs, OAuth, OIDC, or SAML are approved
- replay cache or replay protection runtime is approved
- auth endpoints, OpenAPI security, SDK/CLI runtime surfaces, connector runtime, operator writes, module activation, sandbox execution, package manifests, lockfiles, migrations, v0.2 tags, or v0.2 releases are added

AION-161 intentionally creates no full-check wrapper.
