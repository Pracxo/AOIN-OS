# Production Auth Release Gates

Production auth runtime cannot be enabled until every gate below is satisfied.
AION-098 adds no runtime implementation and keeps `production_auth_enabled`
false.

AION-099 does not satisfy or bypass these gates. It adds disabled status,
mock-claims preview, and audit proof only; production auth remains disabled.

| Gate | Required Evidence | Blocker Behavior |
| --- | --- | --- |
| threat model approved | reviewed `docs/auth/production-auth-threat-model.md` | block runtime auth |
| provider selected | approved provider decision and fallback posture | block provider integration |
| token/session storage design approved | approved storage decision and migration plan | block token/session storage |
| CSRF/CORS plan approved | browser/API protection review | block cookie or browser auth flow |
| audit correlation tested | provider subject to ActorContext to policy to trace test | block release |
| role mapping tested | group/claim mapping and fail-closed tests | block operator access |
| revocation tested | provider and local revocation proof | block release |
| disabled-by-default prototype green | AION-099 mock-only prototype checks | block runtime enablement |
| security review complete | signed review record | block release |
| no secret leakage | examples, logs, telemetry, docs, and audit scans | block release |
| rollback plan | documented disablement and recovery path | block release |

No gate can be waived by the Operator Console, local auth simulation,
ActorContext headers, reverse proxy headers, policy shortcuts, or action
authorization decisions.
