# Shadow Activation Data Boundary

AION-180 records `AION-180-SI-0007` as the sole active implementation authorization for AION-181. It authorizes construction of a disabled controlled shadow activation control plane only. It does not authorize activation, runtime enablement, source mutation, Git mutation, approval creation, merge, promotion, canary, deployment, model training, a v0.2 tag, or a v0.2 release.

AION-SOE-001 remains successful advisory evidence and is not an approval. `AION-177-SI-0006` remains closed, expired, and non-reusable.


Authorized future adapters are `in_memory_redacted_snapshot_adapter` and `explicit_local_shadow_evidence_bundle_adapter`. The local evidence bundle adapter must require an explicit absolute file path outside the repository, reject traversal, symlink escape, hidden files, directories, URLs, network paths, device files, oversized files, unknown schema fields, protected text, credentials, tokens, cookies, private keys, personal data, source patches, and raw diffs. It remains read-only and performs no directory discovery.
