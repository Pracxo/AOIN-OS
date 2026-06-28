# Production Auth Threat Model

AION-098 records the production auth threat model before runtime auth exists.
Each threat has a control, required future test, and no-go condition.

| Threat | Control | Required Future Test | No-Go Condition |
| --- | --- | --- | --- |
| token theft | keep token values out of public contracts, logs, telemetry, docs, and examples | redaction and log scan test | token value appears outside auth boundary |
| session fixation | rotate future session after auth and bind it to validated actor context | session rotation test | session id accepted before validated auth |
| CSRF | require CSRF design before cookie-based flows | CSRF negative test | state-changing request succeeds without CSRF control |
| CORS misconfiguration | allow only approved origins and fail closed | CORS deny-list test | untrusted origin can use auth context |
| cookie misuse | require secure, SameSite, expiry, and rotation policy before cookies | cookie attribute test | cookie lacks required controls |
| redirect attack | validate redirect targets and state/nonce | redirect negative test | unapproved redirect target accepted |
| privilege escalation | fail-closed role and group mapping | role escalation test | unmapped role grants operator privilege |
| stale role mapping | require refresh and revocation behavior | stale group revocation test | revoked group keeps access |
| audit mismatch | correlate provider subject, ActorContext, policy, and trace | audit correlation test | auth action lacks traceable audit link |
| reverse proxy spoofing | strip inbound identity headers and verify proxy trust boundary | spoofed header test | client-supplied identity header trusted |
| localhost origin confusion | separate dev-only local auth from production auth | origin confusion test | local-only context accepted as production |
| provider outage | define fail-closed and recovery posture | provider unavailable test | provider outage grants access |
| account lockout | define recovery and support workflow | lockout simulation | bypass added without audit |
| break-glass misuse | require approval, audit, expiry, and scoped emergency access | break-glass audit test | emergency access persists or bypasses policy |

AION-098 implements none of these runtime controls. They are future release
requirements.
