# Source Registry Indexes And Queries

AION-207 builds deterministic exact indexes from validated registry records.

Indexes cover:

- record ID
- source snapshot fingerprint
- content SHA-256
- provenance fingerprint
- citation ID
- lineage and independence-group ID
- source classification
- retrieval timestamp

Index values are immutable tuples of existing record IDs. Duplicate index entries and references to missing records are rejected.

Queries are exact and bounded to 100 results. Allowed query kinds are record ID, snapshot fingerprint, content hash, provenance fingerprint, citation ID, lineage group ID, source class, and retrieval time range.

There is no fuzzy search, semantic search, source-body search, claim ranking, truth ranking, knowledge ranking, network query, backend request, or persistent state mutation.
