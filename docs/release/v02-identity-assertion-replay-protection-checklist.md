# v0.2 Identity Assertion Replay Protection Checklist

- [x] AION-163-PA-0007 referenced.
- [x] Replay key schema and domain separator fixed.
- [x] Replay policy, result, evidence, and pipeline schemas created.
- [x] Dedicated SQLAlchemy table and exact indexes defined.
- [x] Repository defaults to `auto_create=false`.
- [x] Insert-first claim implemented.
- [x] Replay and identifier-collision outcomes fail closed.
- [x] Missing schema and repository failure outcomes fail closed.
- [x] Retention and explicit cleanup implemented.
- [x] Offline verification pipeline calls replay only after cryptographic success.
- [x] Evidence is redacted and fingerprinted.
- [x] No runtime registration, API route, config field, SDK resource, CLI command, package file, lockfile, migration, v0.2 tag, or release added.
## AION-164 Implementation Note

AION-164 adds implementation evidence while keeping dependency, migration, runtime, tag, and release prohibitions in force.
