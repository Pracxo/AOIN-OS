# Source Registry Append-Only Semantics

AION-207 permits pure in-memory append simulation only.

The current authorization sets `maximum_registry_write_batch=0`. That value is unchanged. Any persistent-write request fails closed and returns a decision with `persistent_write_applied=false`.

Append rules:

- A record sequence begins at one.
- New records must be contiguous.
- The previous-record fingerprint must match the current chain head.
- The same record ID with the same fingerprint is idempotent replay.
- The same record ID with a changed payload is rejected.
- Corrections create a new record ID, increment the version by one, and reference the superseded record.
- Superseded records remain present.
- Updates, deletes, truncation, compaction, overwrite, file save, database commit, Git mutation, PR creation, merge, deployment, and model training are unavailable.
