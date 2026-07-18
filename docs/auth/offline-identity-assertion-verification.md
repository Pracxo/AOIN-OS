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


## AION-163 Replay Protection Authorization Update

AION-163 records AION-162 PR #72 and corrective PR #73 as the completed offline verification delivery, closes `AION-161-PA-0006` as inactive, consumed, expired, and non-reusable, and creates `AION-163-PA-0007` as the sole active authorization for AION-164 persistent identity-assertion replay protection. The next critical path is AION-164. Runtime request authentication, ActorContext application, RequestIdentityContext application, dependency changes, migrations, production schema auto-create, package files, lockfiles, v0.2 tags, and v0.2 releases remain blocked.
## AION-164 Replay Protection

Offline verification now has an internal follow-on replay-protection pipeline for tests and future authorized integration. The verifier itself remains unchanged and does not perform request authentication. Replay protection rejects duplicate or colliding assertions through a dedicated persistent ledger.
