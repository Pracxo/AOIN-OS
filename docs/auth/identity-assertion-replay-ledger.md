# Identity Assertion Replay Ledger

The replay ledger uses the dedicated table `aion_identity_assertion_replay_claims`.

Columns:

- `replay_key`
- `issuer_fingerprint`
- `assertion_fingerprint`
- `claimed_at`
- `assertion_expires_at`
- `retain_until`
- `created_at`

The primary key is `replay_key`. Required indexes are `ix_aion_identity_assertion_replay_retain_until`, `ix_aion_identity_assertion_replay_claimed_at`, and `ix_aion_identity_assertion_replay_assertion_expires_at`.

The repository uses an insert-first algorithm. It never selects before the initial insert, never deletes and replaces a replay record, never uses a process-global in-memory replay set, and never reuses the generic idempotency table. `auto_create` defaults to false; test code may pass `auto_create=true`, but production schema provisioning remains a future migration task.

Cleanup is explicit through `purge_expired(now, limit)`. No claim, protection, or pipeline call starts cleanup automatically.
