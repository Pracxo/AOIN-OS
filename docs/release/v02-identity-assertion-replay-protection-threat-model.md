# v0.2 Identity Assertion Replay Protection Threat Model

- check-then-insert race
- concurrent duplicate claims
- two repository instances using one database
- database rollback after unique-constraint conflict
- assertion-ID reuse
- same assertion ID with changed payload
- same assertion ID under different issuer
- replay-key derivation ambiguity
- replay-key domain separation
- fingerprint mismatch
- verification-bundle substitution
- unverified assertion reaching repository
- database unavailable
- schema unavailable
- cleanup and claim race
- clock skew
- retention underflow
- retention overflow
- stale record remaining after retention
- raw assertion persistence
- raw claim persistence
- raw identifier logging
- SQL exception leakage
- runtime in-memory store substitution
- request integration before formal authorization
- replay success misrepresented as request authentication
## AION-164 Implementation Note

AION-164 covers duplicate replay, identifier collision, missing schema, repository failure, cleanup failure, and expired assertion paths with fail-closed evidence.
