# v0.2 Actor Context Trust Boundary Evidence Matrix

| Evidence | Source |
| --- | --- |
| Current source behavior | `identity/dev_auth.py` reads identity-bearing headers in the non-development branch. |
| AION-158 implementation | PR 68, feature `767fd9b228b00b04569df2e3b1b3f6bc9ecd846f`, merge `f792c92e1d8a73ec8e7377b5d59269dea359006d`. |
| AION-157 lifecycle | `AION-157-PA-0004` inactive, consumed, expired, non-reusable. |
| AION-159 authorization | `AION-159-PA-0005` active for AION-160. |
| AION-160 required evidence | fail-closed actor context, development isolation, request identity precedence, request context correlation, route regression tests, privilege escalation regression. |
| Reviewer | security, runtime governance, platform, audit. |
| ADR | `docs/adr/0150-v02-actor-context-trust-boundary-authorization.md`. |
| Gate | `scripts/v02-actor-context-trust-boundary-authorization-check.sh`. |
| No-go gate | `scripts/v02-actor-context-trust-boundary-authorization-no-go-regression.sh`. |
| Lifecycle state | exactly one active authorization: `AION-159-PA-0005`. |
| Remediation permissions | actor-context trust-boundary remediation permissions only. |
| Runtime state | runtime guard held, no authenticated requests, no production auth runtime. |
| Blocker | actor-context trust-boundary remediation remains until AION-160 merges. |
| Expiry | AION-160 merge or explicit revocation. |
| Revocation | follow-up record referencing `AION-159-PA-0005` with guards held. |
