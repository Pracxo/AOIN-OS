# Offline Identity Assertion Verification

AION-162 implements the `AION-161-PA-0006` authorized offline Ed25519 identity
assertion verification core.

The implementation state is `implemented_unintegrated`. The verifier checks a
strict assertion envelope with fixed Ed25519 semantics, canonical payload bytes,
domain separation, exact public-key ID selection, issuer and audience equality,
UTC assertion times, assertion lifetime, assertion ID syntax, claim limits, and
safe metadata constraints.

The verifier does not authenticate requests. It does not parse headers, cookies,
or request bodies, does not apply ActorContext, does not apply
RequestIdentityContext, does not register middleware, and does not add an API
route or OpenAPI security scheme.

Runtime private signing material is absent. Signing keys are test-only,
ephemeral, in memory, and never serialized. Runtime code imports only public
verification key APIs.

Replay protection is intentionally absent in AION-162. Repeated verification of
the same assertion is allowed and every result states
`replay_check_performed=false` and
`replay_protection_required_before_request_integration=true`.
