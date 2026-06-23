# Operator Auth Threat Model

| Threat | Current v0.1/AION-093 Control | Future Required Control | No-Go Condition |
| --- | --- | --- | --- |
| unauthenticated console access | static console is local and design-only | local session gate and origin checks | hosted console without auth |
| local machine compromise | no production auth claim | secure local setup guidance and audit warnings | privileged console on shared machine |
| role confusion | documented roles only | role provisioning and policy binding | ambiguous role maps |
| privilege escalation | no runtime role mutation | audited role change flow | self-service admin upgrade |
| stale session | no sessions implemented | idle and absolute timeout | no timeout model |
| token leakage | no tokens implemented | token handling and rotation design | token in browser-readable storage |
| secret display | redaction docs and checks | view-level redaction enforcement | secret-like value visible |
| raw prompt exposure | no raw prompt display allowed | prompt redaction gate | raw prompt visible |
| hidden reasoning exposure | no hidden reasoning display allowed | hidden reasoning detection | hidden reasoning visible |
| CSRF against future local server | no login or write server added | CSRF protection | write path without CSRF design |
| clickjacking against future UI | no hosted UI | frame restrictions | embeddable privileged UI |
| API origin confusion | static console limits local origins | strict CORS and origin policy | wildcard origin policy |
| localhost trust abuse | localhost is not authority | explicit local trust model | localhost bypasses policy |
| policy bypass | policy remains authoritative | policy-bound auth middleware | direct privileged shortcut |
| audit tampering | audit remains separate | tamper-evident auth audit trail | unaudited privileged access |

This threat model is intentionally conservative. AION-093 cannot claim auth
readiness until these future controls are designed, implemented, and gated.
