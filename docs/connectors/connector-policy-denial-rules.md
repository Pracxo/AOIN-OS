# Connector Policy Denial Rules

AION-111 defines explicit denial rows for future connector runtime actions.
The denial rules make future unsafe action names visible to policy tests while
keeping the action result fail-closed.

Denied action keys:

- `connector.runtime.enable`
- `connector.external.call`
- `connector.credentials.store`
- `connector.tokens.store`
- `connector.activate`
- `connector.route.register`
- `connector.tool.execute`
- `connector.write.execute`
- `connector.provider.call`

Each denial carries `runtime_allowed=false`, `external_call_allowed=false`,
`credential_access_allowed=false`, `token_access_allowed=false`, and
`activation_allowed=false`.

These denial rows are not hidden skips. They are positive evidence that future
runtime work must pass a new implementation brief, operator review, audit and
provenance review, and no-go regression gates before any connector runtime can
exist.

## AION-113 Credential Denials

AION-113 adds explicit denials for future credential store/read/rotate/revoke,
token store/read, secret materialization, OAuth callback/exchange, OIDC login,
SAML assertion, and external identity bind actions.
