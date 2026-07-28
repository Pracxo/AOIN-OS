# Local Persistence Backup Restore

Backup and restore must be explicitly operator invoked. Backups require a manifest and integrity validation. Restore targets a new empty path only, never overwrites the active store, validates fingerprints, schema, integrity, ledger hashes, foreign keys, receipts, approval bindings, and projection bindings, and never switches active store automatically.
