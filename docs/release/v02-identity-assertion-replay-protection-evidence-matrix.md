
# v0.2 Identity Assertion Replay Protection Evidence Matrix

| Evidence | Status |
| --- | --- |
| AION-161 historical closeout | inactive, consumed, expired, non-reusable |
| AION-162 PR #72 | recorded |
| AION-162 PR #73 | recorded |
| AION-163-PA-0007 | sole active authorization |
| Replay key contract | issuer plus assertion ID, domain separated |
| Atomic claim | unique insert required |
| Identifier collision | required for changed payload under same issuer/assertion ID |
| Persistence | hashes and timestamps only |
| Dependency change | prohibited |
| Migration | prohibited |
| Production schema auto-create | prohibited |
| Runtime integration | prohibited |
| Request authentication | false |
| v0.2 tag and release | absent |
