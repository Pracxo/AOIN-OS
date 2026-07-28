# ADR 0186: Approval-Bound Knowledge-Promotion Transaction and Cognitive-Memory Projection-Planning Core

## Status
Accepted for AION-222.

## Decision
AION OS implements the AION-221-GLM-0001 scoped knowledge-promotion transaction core as deterministic planning only. The core may compute reviewable transaction plans and cognitive-memory projection plans from verified-knowledge candidates and existing approval evidence, but it must not persist knowledge, write memory, create beliefs, create approvals, call external systems, or register runtime services.

## Consequences
AION-223 remains responsible for formal closeout and any future persistence authorization decision. AION-222 output may mark a transaction structurally ready for future persistence review, but persistence is not authorized by this ADR or implementation.
