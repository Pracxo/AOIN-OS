# v0.2 Production Auth Core Stabilization No-Go

AION-154 must fail if any of these appear:

- production-auth runtime enabled
- login, logout, callback, token, session, credential, OAuth, OIDC, or SAML
  routes added
- `services/brain-api/src/aion_brain/api/production_auth.py` created
- credentials, passwords, tokens, cookies, provider payloads, raw prompts, or
  hidden reasoning stored
- network clients, external calls, provider SDKs, package files, lockfiles, or
  migrations added
- SDK or CLI production-auth runtime source added
- operator write execution, connector runtime, module activation, or sandbox
  execution enabled
- runtime guard release approved
- implementation approval broadened beyond
  `disabled-production-auth-core-stabilization`
- `v0.2`, `v0.2.0`, `aion-v0.2`, or `aion-v0.2.0` tag or release created

Allowed AION-154 source changes are limited to internal disabled production-auth
contracts, core services, config mapping, kernel diagnostics, docs, examples,
static-console read-only evidence, tests, and gate scripts.
