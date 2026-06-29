# Operator Platform Risk Register

| Risk | Current control | Check script | Residual risk | No-go condition |
| --- | --- | --- | --- | --- |
| Frontend dependency creep | Static console is plain HTML, CSS, and JavaScript with package files blocked. | `./scripts/static-console-safety-check.sh` | Future UI work could add package files accidentally. | Any package file, lockfile, frontend config, install instruction, or build step appears before a UI ADR. |
| Hidden write action | Operator views expose descriptors and previews only. | `./scripts/operator-actions-check.sh` | New buttons or request previews could imply writes. | Any enabled write control, mutating HTTP verb, or action proposal execution path appears. |
| Activation leakage | Module lifecycle data keeps activation false and blockers visible. | `./scripts/module-lifecycle-dashboard-check.sh` | Future module UI work could hide blockers. | Any activation, capability activation, runtime registration, or code loading control appears. |
| Auth runtime enablement | Disabled auth runtime remains hard-off with mock-only preview. | `./scripts/auth-runtime-check.sh` | Future auth work could blur prototype and runtime boundaries. | Production auth, login/logout, token issuance, cookie issuance, external IdP runtime, or real session acceptance appears. |
| Credential/session storage | Local auth and session previews are synthetic and read-only. | `./scripts/local-auth-check.sh` and `./scripts/local-session-check.sh` | Demo labels could imply stored identity state. | Any credential store, persisted browser session, token store, cookie store, or session writer appears. |
| Raw prompt exposure | Console redaction rules block protected source payloads. | `./scripts/static-console-safety-check.sh` | New demo data could accidentally include protected prompt content. | Any raw prompt field or source prompt rendering appears. |
| Hidden reasoning exposure | Console redaction rules block private reasoning markers. | `./scripts/static-console-safety-check.sh` | New evidence text could use unsafe internal reasoning labels. | Any hidden reasoning or chain-of-thought rendering appears. |
| Provider call leakage | Provider dashboard remains hardening evidence only. | `./scripts/provider-dashboard-check.sh` | Future provider work could add call controls too early. | Any provider invocation, model call, provider credential flow, or external model call control appears. |
| External URL call | Static console permits only local API origins. | `./scripts/static-console-safety-check.sh` | Future assets could add external scripts, styles, or URLs. | Any non-local URL, external script, external stylesheet, external notification, or web call appears. |
| Stale demo data | Evidence examples and demo JSON are checked locally. | `./scripts/operator-platform-checkpoint.sh` | Demo data can lag behind docs if not checked together. | Evidence examples are invalid, missing required areas, or claim a passing status without scripts. |
| Policy bypass | Dry-run authorization keeps denials visible. | `./scripts/action-authorization-check.sh` and `./scripts/role-filter-check.sh` | Role filtering could be mistaken for production authorization. | Any role path grants execution, activation, external calls, or privileged bypass. |
| Audit bypass | Operator console contract audits fail closed on unsafe files. | `./scripts/operator-console-contract-check.sh` | New evidence files need explicit checkpoint validation. | Any evidence file escapes both legacy contract checks and the AION-101 checkpoint script. |
| Auth prototype drift | AION-104 freezes the local auth prototype review and no-go regression pack. | `./scripts/auth-prototype-review.sh` and `./scripts/auth-no-go-regression.sh` | Future auth work could skip the disabled/mock-only baseline. | Any production auth, login/logout, credential, token, cookie, session persistence, provider SDK, external identity runtime, migration, API router, or bypass appears before a later implementation ADR. |

## AION-102 stabilization control

`./scripts/operator-platform-regression.sh` and
`./scripts/operator-platform-freeze-gate.sh` now aggregate these controls into
one long-running regression matrix and one checkpoint freeze gate. Any failed
row remains a release blocker and must be fixed forward without bypassing the
underlying local check.

## AION-104 auth review control

`./scripts/auth-prototype-review.sh` and
`./scripts/auth-no-go-regression.sh` now aggregate the local auth, session,
role, action authorization, production auth architecture, disabled auth
runtime, static console, docs, and no-go controls into an auth-specific
pre-implementation gate.
