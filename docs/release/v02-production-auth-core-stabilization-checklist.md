# v0.2 Production Auth Core Stabilization Checklist

- [x] Phase 0 CI portability repairs retained.
- [x] `aion-v0.1.0` immutable tag recovery and SHA verification retained.
- [x] AION-151 implementation lineage preserved.
- [x] AION-153 stabilization lineage added separately.
- [x] Schema, canonicalization, policy, and reason-code registry versions added.
- [x] Canonical JSON serialization uses only the Python standard library.
- [x] Evidence fingerprints added to status, decision, audit, provenance, and diagnostics.
- [x] Reason-code registry centralized and immutable.
- [x] Unknown internal operations fail closed.
- [x] Evidence models are frozen and metadata is immutable.
- [x] Idempotency and concurrency coverage added.
- [x] Prohibited configuration matrix added.
- [x] Redaction coverage hardened.
- [x] Diagnostics remain redacted safety state only.
- [x] Kernel construction remains stable.
- [x] Public production-auth routes remain absent.
- [x] Performance smoke coverage is dependency-free.
- [x] Runtime, release, tag, package, lockfile, migration, SDK, CLI, provider, external-call, operator, connector, module, and sandbox boundaries remain blocked.
