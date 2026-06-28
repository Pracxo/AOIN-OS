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

## AION-095 Local Session Runtime Boundary

Local session preview runtime is stateless. It may generate synthetic preview
records and expiry metadata, but it must not create login/logout routes, store
credentials, issue tokens or cookies, persist browser session state, bypass
policy, bypass ActorContext, or grant privileged actions.

## AION-096 Role Filter Runtime Boundary

Role filtering is an in-process read-only projection over console view models.
It may remove allowed descriptors or restrict sections, but it must not create
runtime auth, mutate source records, add browser state, or grant privileged
actions.
