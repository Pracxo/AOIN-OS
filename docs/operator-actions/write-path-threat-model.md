# Operator Action Write-Path Threat Model

## Purpose

AION-107 defines threats that must block any future operator action write path
until matching controls are implemented and release-gated.

| Threat | Entry point | Current control | Future required control | No-go condition |
| --- | --- | --- | --- | --- |
| approval bypass | Review or approval record | Approval is review evidence only and does not execute. | Non-expired approval with reviewer separation, revocation, and audit. | Any approval grants execution without policy and authorization. |
| policy bypass | Role filter, preview, connector metadata, or model output | Policy and dry-run authorization fail closed. | Current policy decision at execution time and deny-wins enforcement. | Any write proceeds without a current allow decision. |
| model-generated tool execution | Model output or action proposal | Model output cannot execute tools. | Proposal broker that can draft intent only, never execute. | Model output invokes tools, connectors, or target writes. |
| confused deputy | Connector, system service, or reviewer flow | Connectors and actions are dry-run only. | Scoped actor context, target binding, and policy input validation. | Service executes with broader authority than requester scope. |
| replayed approval | Approval reference reused after context changes | Approval is not executable. | Nonce, expiry, stale-preview check, and target-drift check. | Expired or replayed approval reaches execution readiness. |
| stale preview | Preview reused after target or policy changes | Preview remains descriptive only. | Preview freshness window and mandatory recompute. | Stale preview becomes executable. |
| target drift | Target changes between preview and future execution | No execution target exists. | Target identity, precondition checks, and drift blocker. | Target drift ignored during execution readiness. |
| irreversible action | Delete-like or non-undoable write | Hard delete is forbidden. | Irreversible class, dual control, confirmation, and compensating plan. | Irreversible action lacks classification and confirmation. |
| rollback failure | Rollback unavailable or fails | Rollback execution absent. | Rollback plan, test evidence, fallback review, and audit. | Write path lacks rollback or compensating action. |
| audit tampering | Audit write, correction, or redaction | Audit is append-only and redacted. | Tamper-evident audit links and immutable provenance refs. | Audit record missing, mutable, or bypassed. |
| privilege escalation | Role, session, or permission mapping | Local roles are preview-only and fail closed. | Production auth, role mapping, scope resolution, and deny-wins policy. | Role path grants write, activation, external calls, or bypass. |
| connector boundary bypass | Connector or target call | Connector runtime and external calls are absent. | Connector trust, credential, egress, ingress, and release gates. | External call executes without connector boundary. |
| external call leakage | Provider, connector, notification, or target egress | External calls remain disabled. | Egress guard, redaction, policy, approval, and audit. | Raw prompts, hidden reasoning, secrets, or protected data leave AION. |

## Current posture

AION-107 keeps all write-path threats blocked by absence of execution. Future
work must implement the required controls before changing that posture.
