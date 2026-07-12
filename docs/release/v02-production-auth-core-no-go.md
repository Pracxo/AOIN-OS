# v0.2 Production Auth Core No-Go

AION-152 no-go checks reject:

- new production-auth API routers
- login, logout, callback, token, session, credential, OAuth, OIDC, or SAML routes
- credential, password, token, session, or cookie storage
- provider clients, provider SDKs, external calls, or network clients
- package files, lockfiles, migrations, SDK runtime resources, or CLI runtime commands
- operator write execution, connector runtime, module activation, or sandbox execution
- second approved authorization records or scope expansion beyond `disabled-production-auth-core`
- `v02` or `aion-v0.2` tags and releases

Allowed implementation-presence state is limited to exact AION-152 evidence:

- `production_auth_core_implemented=true`
- `production_auth_core_state=implemented_disabled`

This implementation-presence state is not runtime approval.
