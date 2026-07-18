# v0.2 Identity Assertion Replay Protection Security Evidence

AION-164 preserves the offline verification boundary and adds replay rejection before future request integration.

Security evidence:

- The replay key is not the assertion fingerprint and does not include signature or key ID.
- Changed payload with the same issuer and assertion ID is rejected as `identifier_collision`.
- Duplicate valid assertion is rejected as `replay_detected`.
- Missing schema and repository failure return fail-closed evidence.
- Cleanup failure raises only the fixed `identity_assertion_replay_cleanup_failed_closed` reason code.
- Evidence includes mandatory runtime-boundary reason codes on every replay result.
- Examples and static console data are synthetic and read-only.

Runtime hold:

- `request_authenticated=false`
- `actor_context_applied=false`
- `request_identity_context_applied=false`
- `runtime_effect=false`
- `runtime_integration_allowed=false`
