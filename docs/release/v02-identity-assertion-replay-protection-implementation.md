# v0.2 Identity Assertion Replay Protection Implementation

AION-164 implements the AION-163-PA-0007 replay-protection core.

Implemented scope:

- Strict replay contracts and reason-code registry.
- Domain-separated replay-key derivation from issuer plus assertion ID.
- Issuer and assertion fingerprints without raw identifier persistence.
- Dedicated SQLAlchemy replay ledger.
- Insert-first unique-constraint claim semantics.
- Replay detection and identifier-collision classification.
- Repository and schema failures that fail closed.
- Explicit retention cleanup.
- Offline verifier plus replay pipeline.
- Redacted audit, provenance, diagnostics, and deterministic evidence fingerprints.

Not implemented:

- Request authentication.
- ActorContext application.
- RequestIdentityContext application.
- Middleware, API routes, OpenAPI security schemes, SDK or CLI runtime resources.
- Provider discovery, JWKS fetch, external calls, credentials, tokens, sessions, package changes, lockfiles, migrations, v0.2 tags, or releases.
