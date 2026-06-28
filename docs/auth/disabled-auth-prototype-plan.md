# Disabled Auth Prototype Plan

AION-099 may create a disabled production auth prototype only. The prototype is
not production auth and must not be enabled by default.

The implemented AION-099 surface is documented in
`disabled-production-auth-prototype.md`, `auth-runtime-gate.md`,
`mock-claims-adapter.md`, `auth-runtime-audit.md`, and
`auth-runtime-no-go.md`.

## Required Prototype Boundaries

- disabled runtime flags
- no default enablement
- mock provider only
- no external call
- no real login
- no real token
- synthetic claims only
- backend policy integration
- audit capture
- release gate before enablement

## Flag Posture

`production_auth_enabled` remains false. Any AION-099 flags must default false
and must fail closed when absent.

## Mock Provider Only

The prototype may use static synthetic claims for local tests. It must not use
OIDC, SAML, LDAP, Active Directory, Passkey, WebAuthn, cloud IAM, or any
provider SDK at runtime.

## Policy And Audit Integration

The prototype must prove how mapped claims reach ActorContext, role matrix,
policy, audit, and dry-run action authorization without granting writes,
execution, activation, external calls, or provider access.

## Release Gate Before Enablement

Moving beyond a disabled prototype requires the production auth release gates,
security review, provider selection, token/session decision, CSRF/CORS plan,
audit correlation tests, role mapping tests, revocation tests, no secret
leakage proof, and rollback plan.
