# Identity Assertion Public-Key Registry

AION-162 adds an immutable public-key registry for offline Ed25519 identity
assertion verification.

The registry accepts only `identity-assertion-public-key/v1` records with exact
key IDs, exact issuer binding, unpadded base64url public keys, UTC activation
windows, revocation state, and safe metadata. Key IDs are ASCII only and never
use fallback syntax.

Resolution is fail closed:

- unknown key ID: rejected
- issuer mismatch: rejected
- revoked key: rejected
- inactive key: rejected
- retired key: rejected

The registry does not contact JWKS endpoints, discover providers, fetch keys
over the network, or load private material. Key rotation is represented by
multiple public keys with explicit active intervals and exact key IDs.


## AION-163 Replay Protection Authorization Update

AION-163 records AION-162 PR #72 and corrective PR #73 as the completed offline verification delivery, closes `AION-161-PA-0006` as inactive, consumed, expired, and non-reusable, and creates `AION-163-PA-0007` as the sole active authorization for AION-164 persistent identity-assertion replay protection. The next critical path is AION-164. Runtime request authentication, ActorContext application, RequestIdentityContext application, dependency changes, migrations, production schema auto-create, package files, lockfiles, v0.2 tags, and v0.2 releases remain blocked.
