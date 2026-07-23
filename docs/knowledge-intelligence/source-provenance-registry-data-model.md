# Source Provenance Registry Data Model

The AION-207 data model is a metadata envelope with `record_id`, `record_kind`, `sequence_number`, `record_version`, optional supersession reference, source classification metadata, retrieval metadata, lineage references, citation references, policy status, payload fingerprint, previous-record fingerprint, and record fingerprint. The model is append-only, deterministic, immutable, and in-memory only. It stores zero source body bytes in the repository and applies no persistent registry write.

Example envelope: `examples/knowledge-intelligence/source-registry-record-envelope.json`.
