# v0.2 Production Auth Stabilization Authorization No-Go

Status: `locked`

The AION-153 authorization must fail if any of these appear:

- more than one active approved production-auth authorization tuple
- an unknown approved authorization transaction
- a partially approved record
- AION-151 marked active, reusable, unconsumed, or unexpired
- AION-153 marked consumed, expired, inactive, or reusable
- scope wider than `disabled-production-auth-core-stabilization`
- runtime implementation approval or production-auth runtime enablement
- login, logout, callback, credential, password, token, session, cookie,
  OAuth, OIDC, SAML, external identity provider, external call, provider SDK,
  operator write, connector, module activation, or sandbox approval
- package file, lockfile, migration, API runtime route, SDK resource, CLI
  command, v0.2 tag, or v0.2 release creation
- protected material, secret values, token values, or private reasoning text

AION-153 does not weaken the AION-151 or AION-152 gates. The old authorization
remains approved historical evidence, but it is inactive and consumed.
