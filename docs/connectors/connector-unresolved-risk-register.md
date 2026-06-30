# Connector Unresolved Risk Register

## Purpose

This register keeps future connector risks visible after the AION-115
checkpoint. The risks remain unresolved because connector implementation is not
approved.

| Risk | Current mitigation | Future evidence required |
| --- | --- | --- |
| credential exfiltration | Credential storage and runtime credential access remain disabled. | Credential store ADR, rotation/revocation tests, redaction audit. |
| prompt injection through connector ingress | Ingress remains preview-only and untrusted. | Ingress parser, redaction, provenance, and policy enforcement evidence. |
| external call data leakage | External calls and network clients remain absent. | Egress allowlist, data minimization, audit, and rollback evidence. |
| sandbox escape | Sandbox execution remains absent. | Sandbox isolation model, resource limits, escape tests, and kill switch. |
| policy bypass | Policy catalog denies runtime allow paths. | Runtime policy enforcement tests and fail-closed audit. |
| audit bypass | Release evidence is local and review-only. | Tamper-evident connector audit records and replay evidence. |
| stale connector response trust | Simulator responses are synthetic and not trusted. | Freshness, provenance, replay, and stale-data invalidation rules. |
| overbroad scopes | Capability and credential scopes remain design-only. | Scope minimization review and operator approval matrix. |
| provider impersonation | Provider SDKs and external identity runtime remain absent. | Provider identity verification and provenance checks. |
| dependency confusion | Package files and connector SDK dependencies remain absent. | Dependency review, lockfile policy, and provenance controls. |
| rollback failure | No connector runtime state exists to roll back. | Rollback plan, compensation plan, and incident drills. |
| operator approval bypass | Implementation approval remains false. | Operator review workflow, policy enforcement, and audit gate evidence. |

## Risk Decision

These risks block implementation approval. They do not block the checkpoint
because the checkpoint keeps runtime behavior disabled.
