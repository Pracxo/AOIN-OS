# 0171: Append-Only Source Provenance Registry Core

## Status

Accepted

## Context

AION-206-KI-0002 authorized AION-207 to implement the append-only source provenance registry core after AION-205 research acquisition. The authorization preserves `maximum_registry_write_batch=0` and keeps source-body persistence, claim verification, knowledge promotion, belief mutation, network access, runtime registration, and persistence disabled.

## Decision

Implement a strict metadata-only registry core with immutable record envelopes, canonical fingerprints, pure in-memory simulated append, explicit synthetic fixture replay, deterministic indexes, bounded exact queries, integrity audits, redacted diagnostics, incident records, and operator-review items.

Do not add an API route, CLI, SDK runtime surface, scheduler, background worker, database, migration, dependency, workflow, source mutation, Git mutation, PR creation, automatic merge, deployment, model training, v0.2 tag, or v0.2 release.

## Consequences

AION OS can register immutable provenance metadata for acquired evidence without treating that evidence as verified fact or promoted knowledge. Persistent registry writes and temporal claim-evidence graph work remain unavailable until a later explicit authorization. AION-208 performs formal closeout and evaluates the next boundary.
