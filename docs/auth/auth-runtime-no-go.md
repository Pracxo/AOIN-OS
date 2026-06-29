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
## AION-104 No-Go Regression

AION-104 records the no-go regression pack in
`docs/auth/auth-no-go-regression-pack.md` and
`examples/auth/auth-no-go-regression-result.json`. The pack fails future work
for login/logout routes, token routes, callback routes, session storage, cookie
issuance, password fields, token fields, credential fields, provider SDKs,
package files, external identity calls, production auth enablement, or auth
bypass.
