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
| Module activation drift | AION-105 freezes the module/plugin activation design review and no-go regression pack. | `./scripts/module-activation-design-review.sh` and `./scripts/module-activation-no-go-regression.sh` | Future module work could treat review evidence as activation permission. | Any code loader, package installer, dynamic import, runtime route registration, capability activation, controlled execution, module write path, policy bypass, or audit bypass appears before a later implementation ADR. |
| Connector runtime drift | AION-106 freezes the external connector boundary design and no-go regression pack. | `./scripts/connector-boundary-design-check.sh` and `./scripts/connector-no-go-regression.sh` | Future connector work could treat metadata or review evidence as permission to call external systems. | Any connector runtime, network client, connector SDK, provider SDK, credential, token storage, dynamic route, external call enablement, policy bypass, or audit bypass appears before a later implementation ADR. |
| Connector policy drift | AION-111 freezes the connector policy action catalog, authorization matrix, dry-run gate, denial rules, and traceability pack. | `./scripts/connector-policy-check.sh` and `./scripts/connector-policy-no-go-regression.sh` | Future connector work could treat policy dry-run evidence as runtime approval. | Any runtime allow path, external call, credential access, token access, activation, route registration, tool execution, write execution, allow command, grant command, or policy bypass appears before a later implementation ADR. |
| Write-path drift | AION-107 freezes write-path architecture and no-go regression before implementation. | `./scripts/operator-action-write-path-design-check.sh` and `./scripts/operator-action-write-path-no-go-regression.sh` | Future action work could treat preview, review, approval, or connector evidence as execution permission. | Any write execution, tool execution, action proposal execution, controlled handoff execution, external call, activation, approval bypass, policy bypass, audit bypass, hard delete, rollback-free execution, or connector-boundary bypass appears before a later implementation ADR. |

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

## AION-105 module activation review control

`./scripts/module-activation-design-review.sh` and
`./scripts/module-activation-no-go-regression.sh` now aggregate the module pack,
Generic Knowledge demo, module lifecycle dashboard, operator platform freeze
gate, UI release gate, docs, boundary, plugin evidence, and no-go controls into
a module activation pre-implementation gate.

## AION-106 connector boundary review control

`./scripts/connector-boundary-design-check.sh` and
`./scripts/connector-no-go-regression.sh` now aggregate connector trust,
credential, egress, ingress, capability declaration, threat model, release gate,
future prerequisite, docs, and no-go controls into an external connector
pre-implementation gate.

## AION-107 write-path architecture control

`./scripts/operator-action-write-path-design-check.sh` and
`./scripts/operator-action-write-path-no-go-regression.sh` now aggregate
write-path architecture, approval boundary, execution boundary, action intent
lifecycle, rollback, separation of duties, threat model, release gates, docs,
examples, and no-go controls into an operator action write-path
pre-implementation gate.
## AION-108 Connector Runtime Risk

The connector runtime risk remains blocked by default. AION-108 adds local
evidence that runtime, external calls, credentials, token storage, activation,
and route registration are disabled, but it does not reduce the future review
required before connector implementation.

## AION-109 Connector Review Risk

AION-109 reduces drift risk by adding explicit no-external-call evidence,
credential/token absence proof, egress/ingress traceability, and a
pre-implementation freeze. The residual risk remains future implementation
scope creep; the mitigation is to keep the review gate and no-go regression
release blocking.

## AION-110 Connector Simulator Risk

AION-110 reduces design ambiguity by adding synthetic dry-run and replay
evidence. Residual risk is treating simulator output as real connector data or
runtime approval. The mitigation is explicit `trusted=false`, hard-off runtime
flags, policy readiness wording, static console no-go evidence, and the
connector simulator no-go regression.

## AION-111 Connector Policy Risk

AION-111 reduces connector authorization ambiguity by adding a read-only policy
catalog, authorization matrix, policy dry-run gate, denial rules, traceability
evidence, SDK/CLI preview access, and static console policy preview data.
Residual risk is treating policy dry-run output as runtime approval. The
mitigation is explicit runtime/external/credential/token/activation denial,
no allow or grant commands, no connector SDK dependency, and the connector
policy no-go regression.

## AION-113 Connector Credential Risk

Credential storage, token storage, secret material, external identity runtime,
and runtime credential access remain critical no-go risks. AION-113 adds
checks and static evidence so these risks stay visible before any future
implementation.
## AION-114 Connector Release Risk

Risk: treating release evidence as implementation approval.

Mitigation: AION-114 keeps `implementation_approved=false` in examples and
static console data. Future connector implementation requires a new ADR and
green release gate evidence.

## AION-115 Connector Checkpoint Risk

Risk: treating the platform checkpoint as permission to start connector
implementation.

Mitigation: AION-115 keeps `implementation_approved=false`, adds an unresolved
risk register, freezes the implementation roadmap, and requires a new explicit
ADR plus gate evidence before any runtime connector work.

## AION-116 Connector Stabilization Risk

Risk: treating the stabilization gate or long-running regression matrix as
runtime approval.

Mitigation: AION-116 keeps `implementation_approved=false`, locks the safety
baseline, and requires future connector implementation to add a new explicit
ADR that passes the stabilization gate before runtime work begins.

## AION-117 Platform Integration Risk

Risk: treating cross-phase checkpoint evidence as approval for production auth,
operator writes, connector implementation, module activation, external calls,
credential storage, token storage, or sandbox execution.

Mitigation: AION-117 keeps all implementation approval booleans false, adds
`./scripts/platform-integration-no-go-regression.sh`, and requires future
runtime work to add explicit ADRs and release gates before implementation.
