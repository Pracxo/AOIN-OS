# Identity Assertion Replay Protection

AION-164 implements persistent replay protection for the offline Ed25519 identity assertion verifier authorized by AION-163-PA-0007.

The replay core is internal and unintegrated. It accepts an already verified `IdentityAssertionVerificationBundle`, derives a domain-separated replay key from issuer plus assertion ID, and claims that key through a dedicated SQLAlchemy ledger. The service does not authenticate a request, apply ActorContext, apply RequestIdentityContext, parse headers, register middleware, expose routes, or enable production-auth runtime behavior.

Outcomes are fail-closed except for the first successful claim:

- `claimed`: a unique insert created the first replay record.
- `replay_detected`: the same replay key and same assertion fingerprint already exist.
- `identifier_collision`: the same issuer plus assertion ID produced a different assertion fingerprint.
- `verification_rejected`, `verification_bundle_mismatch`, `assertion_expired`, `repository_unavailable`, and `schema_unavailable`: no request authentication is produced.

Evidence stores only the replay key, issuer fingerprint, assertion fingerprint, timestamps, outcome flags, fixed reason codes, and deterministic evidence fingerprints. Raw issuer, raw assertion ID, raw assertion, signature, subject, actor ID, workspace ID, roles, permissions, security scopes, metadata, SQL text, and exception text are prohibited.
