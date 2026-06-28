# Future Session Implementation Plan

AION-095 does not implement production sessions. Future session work must remain
blocked until a separate milestone approves production authentication scope.

Required future prerequisites:

- ADR for production auth and session storage
- threat model update
- policy catalog update
- migration review
- cookie and browser-state security review
- credential storage decision
- token issuance decision
- audit and provenance update
- Operator Console UI security review

Until then, local session previews remain synthetic, read-only, local-only, and
non-persistent.
