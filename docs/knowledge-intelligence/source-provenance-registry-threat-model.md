# Source Provenance Registry Threat Model

The registry threat model covers source body leakage, digest spoofing, citation spoofing, lineage tampering, duplicate-source confusion, stale metadata, source classification being mistaken for truth, prompt injection in source metadata, registry overwrite attempts, unauthorized runtime writes, migration drift, API route drift, Git mutation, and knowledge promotion bypass.

Required controls: append-only records, canonical JSON fingerprints, digest-only source references, zero source body persistence, redacted metadata, deterministic tests, no live network requests, no claim verification, no knowledge promotion, no belief mutation, no runtime activation, and no privileged bypass.
