# v0.2 Offline Identity Assertion Verification Security Evidence

Security controls:

- fixed Ed25519 verification only
- no algorithm negotiation
- strict envelope with no `alg`, `algorithm`, `typ`, `jwt`, or `token_type`
- domain-separated canonical JSON signing input
- strict unpadded base64url for signatures and public keys
- public-key-only runtime trust
- exact key ID and issuer matching
- UTC temporal validation
- duplicate claim rejection
- metadata protected-material rejection
- deterministic SHA-256 evidence fingerprints
- redacted audit, provenance, and diagnostic evidence
- no raw assertion, signature, full public key, subject, actor ID, workspace ID,
  roles, permissions, scopes, or metadata in evidence

Runtime boundaries remain disabled and are checked by the AION-162 no-go and
runtime-hold scripts.
