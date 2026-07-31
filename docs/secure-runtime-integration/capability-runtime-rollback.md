# Capability Runtime Rollback

AION-235 rollback is deterministic and local. Closed rollback steps discard transient input and output, discard connector previews, release fixture snapshots, release request records, invalidate pending receipts, close the request and preserve redacted evidence. No external undo or production mutation is available.
