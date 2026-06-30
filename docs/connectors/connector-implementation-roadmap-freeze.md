# Connector Implementation Roadmap Freeze

## Purpose

AION-115 freezes future connector implementation planning until a new explicit
ADR and gate evidence are produced. This freeze prevents checkpoint evidence
from being treated as runtime approval.

## Freeze Statements

- implementation is not approved
- future implementation requires explicit ADR
- future implementation requires production auth decision
- future implementation requires credential store implementation approval
- future implementation requires sandbox implementation approval
- future implementation requires external call release gate
- future implementation requires rollback/audit plan
- future implementation requires operator review and policy enforcement

## Frozen Work Types

The following work types remain blocked:

- connector runtime execution
- external service calls
- credential storage
- token storage
- OAuth/OIDC/SAML runtime
- sandbox execution
- connector activation
- route registration
- provider SDK integration
- connector SDK dependency adoption
- runtime API route expansion
- CLI or SDK command implementation for execution or storage
- migrations for connector runtime state

## Allowed Future Planning Work

Future work may update documentation, threat models, approval criteria, and
review checklists if it preserves the disabled safe state. Any implementation
proposal must add a new ADR and must be reviewed independently of this
checkpoint.

## Required Future ADR Topics

A future implementation ADR must cover:

- production auth dependency and operator identity mapping
- credential store ownership, rotation, revocation, and audit
- sandbox isolation, resource limits, filesystem policy, and network policy
- external call egress control, ingress redaction, and provenance
- policy enforcement, operator review, and fail-closed behavior
- rollback, compensation, incident response, and audit retention
- package dependency review and dependency-confusion controls

## No-Go Conditions

Implementation remains frozen if any of these are missing:

- explicit ADR approval
- green release and no-go regression evidence
- production auth decision
- credential store implementation approval
- sandbox implementation approval
- external-call release gate
- rollback and audit plan
- operator review and policy enforcement evidence

## Freeze Decision

AION-115 freezes the roadmap at checkpoint status. Future connector
implementation starts only after a new ADR and updated gate package prove the
next boundary.

## AION-116 Stabilization Requirement

AION-116 adds a long-running regression matrix and phase freeze gate as a
required input to any future connector implementation ADR. Future implementation
work must pass `./scripts/connector-platform-regression.sh` and
`./scripts/connector-platform-stabilization-gate.sh` before runtime scope can be
reviewed.

## AION-117 Platform Integration Requirement

AION-117 adds the platform integration checkpoint as another required input to
any future connector implementation ADR. Future implementation work must pass
`./scripts/platform-integration-checkpoint.sh`,
`./scripts/platform-integration-freeze-check.sh`, and
`./scripts/platform-integration-no-go-regression.sh` before runtime scope can
be reviewed.
