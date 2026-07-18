
# v0.2 Identity Assertion Replay Protection Persistence Model

AION-164 must use a dedicated SQLAlchemy replay ledger and may not reuse the generic idempotency service as the replay ledger.

## Table

`aion_identity_assertion_replay_claims` stores `replay_key`, `issuer_fingerprint`, `assertion_fingerprint`, `claimed_at`, `assertion_expires_at`, `retain_until`, and `created_at`. The replay key is the primary key. Indexes are required on retain-until, claimed-at, and assertion-expires-at.

## Stored Data

Only hashes and timestamps may be stored. Raw issuer, raw assertion ID, raw assertion, signature, key material, subject, actor, workspace, roles, permissions, security scopes, metadata, request data, verification exception text, and SQL statement text are prohibited.

## Auto-Create

`IdentityAssertionReplayRepository(*, engine: Engine, auto_create: bool = False)` defaults to `auto_create=false`. Test code may set `auto_create=true`. Production runtime code must never call create-all automatically. Missing schema fails closed.
## AION-164 Implementation Note

The implementation uses the documented `aion_identity_assertion_replay_claims` table with exact hash-and-timestamp columns and explicit test-only schema creation.
