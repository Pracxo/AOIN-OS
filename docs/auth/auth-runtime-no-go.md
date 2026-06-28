# Auth Runtime No-Go Rules

The AION-099 auth runtime prototype must not add or enable:

- production auth
- login or logout flows
- OAuth, SAML, OIDC, LDAP, Active Directory, passkey, or WebAuthn providers
- external identity provider calls
- credential collection or storage
- token or cookie issuance
- persistent session state
- provider SDK dependencies
- frontend dependencies or package manager files
- activation, code loading, tool execution, hard delete, or external calls

Mock claims are fixtures only. They are not credentials and they must not be
accepted as proof of identity outside the preview endpoint.

Any future production auth implementation must start from a new explicit
milestone and pass the production auth release gates before any runtime auth is
enabled.

AION-100 adds a static UI release gate that must also remain green before
future UI auth work. The gate blocks login forms, credential fields, token or
cookie fields, session storage, provider-call controls, production auth claims,
frontend dependencies, and external URLs in the static console.
