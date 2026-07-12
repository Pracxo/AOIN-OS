# v0.2 Production Auth Stabilization Scope

Status: `locked`

## Permitted for AION-154

The active AION-153 authorization permits future AION-154 work only inside the
disabled production-auth core stabilization scope:

- internal production-auth core stabilization
- disabled-by-default configuration hardening
- fail-closed policy stabilization
- audit and provenance evidence stabilization
- redacted diagnostics stabilization
- deterministic stabilization tests
- documentation
- read-only static-console status evidence

## Prohibited for AION-154

AION-154 remains prohibited from runtime enablement, login endpoints, logout
endpoints, authentication callback endpoints, credential storage, password
storage, token issuance, token storage, cookie or session persistence, database
migrations, external identity providers, network calls, OAuth runtime, OIDC
runtime, SAML runtime, provider SDK installation, frontend dependencies,
package or lockfile changes, operator write execution, connector runtime,
module activation, sandbox execution, and production release or tag creation.

## AION-153 implementation boundary

AION-153 itself is governance-only. It adds no production-auth implementation
code and creates no runtime route, SDK resource, CLI command, package file,
lockfile, migration, tag, or release.
