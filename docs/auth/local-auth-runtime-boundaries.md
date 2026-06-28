# Local Auth Runtime Boundaries

AION-094 introduces local auth contracts without production auth runtime behavior.

AION-099 keeps local auth separate from the disabled production auth runtime
prototype. Mock claims preview may reuse the local role matrix for preview-only
role decisions, but it does not authenticate, authorize production access, or
create session state.

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

## AION-098 Production Auth Architecture Boundary

AION-098 documents future production auth architecture only. It does not add
production auth runtime, provider SDKs, login/logout routes, credential
storage, token issuance, cookie issuance, session persistence, migrations,
external identity calls, frontend package files, or privileged bypass.
`production_auth_enabled` remains false.
