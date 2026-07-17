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
