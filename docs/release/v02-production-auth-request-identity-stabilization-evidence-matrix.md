# v0.2 Production Auth Request Identity Stabilization Evidence Matrix

Status: `complete`

| Evidence | Required reviewer | Gate | Lifecycle state | Notes |
| --- | --- | --- | --- | --- |
| AION-156 PR 66 | platform reviewer | `production-auth-request-identity-check.sh` | merged | Disabled request identity boundary implemented. |
| AION-155 closeout | runtime governance reviewer | `v02-production-auth-request-identity-stabilization-authorization-check.sh` | consumed | `AION-155-PA-0003` inactive, expired, non-reusable. |
| AION-157 authorization | security reviewer | `v02-production-auth-request-identity-stabilization-authorization-no-go-regression.sh` | active until AION-158 merge | `AION-157-PA-0004` authorizes only disabled request identity stabilization. |
| AION-158 pure ASGI middleware | platform reviewer | `production-auth-request-identity-stabilization-check.sh` | implemented_disabled | `BaseHTTPMiddleware` removed; public class name preserved. |
| Streaming and body passthrough | API reviewer | focused pytest | verified | `receive` and `send` are passed through unchanged. |
| Forged-state and duplicate registration guard | security reviewer | focused pytest | verified | Forged identity state is replaced and duplicate middleware registration fails closed. |
| ADR 0149 | audit reviewer | docs audit | approved | Stabilization decision, runtime restrictions, and authorization expiry recorded. |
| Runtime guard | security reviewer | `production-auth-request-identity-stabilization-runtime-hold.sh` | held | Runtime auth, parsing, endpoints, providers, packages, migrations, SDK/CLI, tags, and releases remain false. |

Expiry: AION-158 merge or explicit revocation of `AION-157-PA-0004`.
Revocation path: create a successor record that removes stabilization
permissions and keeps runtime guards locked.
