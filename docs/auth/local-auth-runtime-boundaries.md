# Local Auth Runtime Boundaries

AION-094 introduces local auth contracts without production auth runtime behavior.

Runtime no-go boundaries:

- no production auth claim
- no login endpoint
- no credential storage
- no session storage
- no cookies
- no token issuing
- no OAuth, SAML, OIDC, LDAP, Active Directory, Passkey, WebAuthn, or cloud IAM runtime code
- no frontend dependency install
- no external service call
- no policy bypass
- no ActorContext bypass
- no execution grant
- no activation grant
- no provider enablement
- no hidden reasoning, raw prompt, or protected value exposure

Local auth may shape development ActorContext semantics and read-only Operator Console filtering. It must not become a source of production authorization.
