# Source Provenance Registry Data Model

The planned AION-207 data model is a metadata envelope with `record_id`, `snapshot_fingerprint`, source classification metadata, retrieval metadata, lineage references, citation references, policy status, and integrity fingerprints. The model is append-only and deterministic. It stores zero source body bytes in the repository.

Example envelope: `examples/knowledge-intelligence/source-registry-record-envelope.json`.
