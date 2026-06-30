# External Connector Boundary Design

## Purpose

AION-106 defines the external connector boundary before any connector runtime
exists. It records the trust, credential, egress, ingress, policy, action
authorization, audit, and operator review requirements that future connector
implementation work must satisfy.

This is design and evidence only. It does not add connector runtime code,
network clients, connector SDKs, provider SDKs, credentials, tokens, external
calls, activation, tool execution, API routes, SDK resources, CLI commands, or
migrations.

## Current State

AION currently stores connector metadata only. Connector validation is local and
does not call external systems. Model provider hardening and prompt egress
guards produce preview evidence only. Local auth, disabled auth runtime, module
activation review, dry-run action authorization, the Operator Platform freeze
gate, and the static console release gate all keep external calls disabled.

## Why No Connector Runtime Exists Yet

External connectors cross an untrusted integration boundary. AION needs a
reviewed connector trust model, credential boundary, egress guard, ingress
guard, policy model, action authorization integration, audit/provenance model,
operator review path, sandbox posture, rollback plan, and release gate before
any connector can call a remote system.

## Connector Lifecycle Proposal

Future connector work should follow this lifecycle:

```text
connector manifest
-> metadata validation
-> trust classification
-> credential boundary review
-> egress preview
-> ingress guard review
-> capability declaration review
-> policy and action authorization review
-> sandbox posture review
-> operator review
-> disabled prototype
-> release gate
-> future runtime activation review
```

The AION-106 terminal state is `runtime_absent`.

## Trust Boundary

Connectors are untrusted by default. Connector manifests, metadata, capability
claims, returned data, status reports, rate-limit claims, and error payloads
must be treated as untrusted until AION validates and normalizes them.

## Credential Boundary

No connector credential is stored in this repository, examples, docs, logs,
static console data, browser storage, or test fixtures. Future credential work
requires a secret-store design, rotation model, revocation model, audit model,
and release gate.

## Egress Boundary

External calls remain disabled by default. Future egress must first produce a
preview that records destination class, scope, payload classification, redaction
state, policy decision, rate-limit posture, operator approval requirement, and
provenance reference. Raw prompts, hidden reasoning, secrets, credentials,
tokens, and protected values must never leave through connector egress.

## Ingress Boundary

Connector responses are untrusted. Future ingress must normalize responses,
classify source trust, scan for secrets, scan for prompt injection, apply
redaction, tag provenance, mark stale data, and route risky results to operator
review before any Brain subsystem trusts the data.

## Policy Integration

Future connector actions must use generic policy actions and fail closed. A
connector cannot self-authorize, create policy bypasses, grant scopes, or turn
metadata claims into active permissions.

## Action Authorization Integration

Connector actions must pass dry-run action authorization before any future
controlled behavior. Connector review cannot execute tools, action proposals,
notifications, external calls, or handoffs.

## Audit/Provenance Requirements

Future connector records must include actor, workspace, connector reference,
scope, policy decision, action authorization decision, egress preview hash,
ingress normalization hash, credential reference metadata, operator decision,
and redacted provenance references.

## Operator Review Requirements

Operators must be able to review connector purpose, declared capabilities,
required scopes, credential needs, egress patterns, ingress risks, rate limits,
policy requirements, sandbox requirements, audit requirements, and rollback
plan before a future connector can be enabled.

## Future Implementation Phases

Future phases should remain disabled by default:

1. Connector ADR and threat model.
2. Credential store and secret reference design.
3. Egress preview and ingress normalization prototype.
4. Dry-run connector simulator.
5. Disabled connector runtime prototype.
6. Operator review and release gate.
7. Future runtime enablement review.

## AION-110 Simulator Relationship

AION-110 implements the dry-run connector simulator as local synthetic evidence
only. It validates shapes and replays local fixtures before runtime
implementation. It does not change the AION-106 terminal state for real
connectors: runtime remains absent for external calls, credential use, token
use, route registration, activation, tool execution, and write execution.

## AION-111 Policy Catalog Relationship

AION-111 adds a connector policy action catalog, authorization matrix, policy
dry-run gate, denial rules, and traceability evidence. These artifacts classify
future connector actions but do not grant runtime permission, external calls,
credential access, token access, route registration, activation, tool
execution, or write execution.

## No-Go Conditions

- connector runtime added without gate
- network call added
- connector SDK dependency added
- provider SDK dependency added
- credentials added
- token storage added
- dynamic route added
- connector activation enabled
- external calls enabled by default
- raw prompt egress allowed
- hidden reasoning egress allowed
- secret egress allowed
- policy bypass
- audit bypass

## AION-107 Write-Path Relationship

The future operator action write path depends on this connector boundary before
any target call can exist. AION-107 does not add connector runtime, network
clients, external calls, credentials, token storage, dynamic routes, activation,
execution, or write target calls. Future execution requires connector or target
boundary evidence, policy, action authorization, approval, audit/provenance,
rollback, and release gates.

## AION-108 Disabled Prototype Relationship

AION-108 adds the disabled prototype step from this lifecycle. It introduces
mock-only manifest validation, egress preview, ingress preview, blockers, API,
SDK/CLI preview access, audit evidence, and static console status. It still
keeps connector runtime, external calls, credentials, token storage, route
registration, activation, execution, and write target calls disabled.

## AION-109 Review Gate Relationship

AION-109 freezes this boundary as review evidence. It adds no runtime
implementation and requires the connector runtime review gate and
no-external-call regression to pass before future connector implementation
planning can proceed.

## AION-113 Credential Boundary Relationship

AION-113 adds connector credential architecture and readiness evidence without
adding credential storage, token storage, secret material, external identity
runtime, or connector runtime credential access. This boundary remains a
blocker before any future connector implementation can request material.
## AION-114 Release Gate Relationship

The external connector boundary is now one input to
`./scripts/connector-release-gate.sh`. The boundary remains design-only and
does not approve runtime execution, external calls, credential/token storage,
sandbox execution, activation, or route registration.
