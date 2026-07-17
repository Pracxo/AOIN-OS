# v0.2 Offline Identity Assertion Verification Threat Model

Task: AION-161

AION-162 must test and document fail-closed behavior for the following threats:

- algorithm confusion, including `none`, HS256, RS256, ES256, untrusted algorithm fields, fallback algorithms, and algorithm negotiation
- key substitution
- unknown key ID
- revoked key
- inactive key
- expired key
- malformed base64url
- non-canonical payload
- signature malleability assumptions
- payload tampering
- issuer confusion
- audience confusion
- clock skew
- expired assertion
- future assertion
- excessive lifetime
- oversized claims
- duplicate roles and permissions
- duplicate security scopes
- assertion replay
- raw assertion leakage
- private-key leakage
- test-key leakage
- runtime integration before replay protection
- provider-network deferral

Required mitigations are fixed Ed25519 verification, domain-separated canonical JSON, exact key ID selection, public-key-only registry entries, strict issuer and audience matching, injected UTC clock, claim limits, redacted evidence, test-only in-memory signing keys, and an explicit statement that valid cryptographic verification is not request authentication.
