# Source Registry Record Envelope

`SourceRegistryRecordEnvelope` wraps one typed source-registry payload.

Each envelope carries:

- AION program, authorization, implementation task, formal closeout task, and scope lineage.
- `sequence_number` beginning at one and increasing by one.
- `record_version` beginning at one.
- `supersedes_record_id` only for correction records.
- `payload_fingerprint` over the typed payload.
- `record_fingerprint` over the envelope excluding the fingerprint field itself.
- `previous_record_fingerprint` to chain the append-only history.

Invariant flags remain fixed:

- `synthetic=true`
- `read_only=true`
- `redacted=true`
- `append_only=true`
- `source_body_present=false`
- `source_body_bytes=0`
- `claim_verified=false`
- `knowledge_promoted=false`
- `belief_created=false`
- `belief_mutated=false`
- `persistent_write_applied=false`
- `runtime_effect=false`

Envelope size remains bounded at 8192 bytes and payload metadata remains bounded at 4096 bytes.
