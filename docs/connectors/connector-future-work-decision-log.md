# Connector Future Work Decision Log

## Purpose

This decision log separates future connector planning that is allowed from
future work that remains blocked after AION-115.

## Approved Work Types

Approved work types are documentation and evidence only:

- checkpoint documentation updates
- threat model refinements
- risk register updates
- read-only static console evidence updates
- JSON example maintenance
- no-go regression improvements
- ADR drafts for future review
- policy denial matrix review

Approved work must keep the connector safe-state booleans disabled and must not
add runtime behavior.

## Blocked Work Types

Blocked work types include:

- connector runtime execution
- external calls and network clients
- provider SDKs and connector SDK dependencies
- credential storage and token storage
- OAuth/OIDC/SAML runtime
- sandbox execution
- connector activation and route registration
- API execution routes
- SDK resources or CLI commands for runtime behavior
- package files, lockfiles, and migrations
- domain connector logic
- tool execution, write paths, and hard delete flows

## Required ADRs

Future implementation requires a new explicit ADR for runtime connector scope.
That ADR must separately approve production auth dependency, credential store
implementation, sandbox implementation, external-call gating, rollback/audit
behavior, and operator review.

## Required Gates

Future implementation must pass:

- connector platform checkpoint
- connector release gate
- connector safety freeze
- connector release no-go regression
- connector runtime review
- connector policy check
- connector sandbox check
- connector credential check
- docs, domain drift, and boundary checks

## Required Evidence

Future implementation evidence must include:

- safe-state delta from AION-115
- egress and ingress controls
- credential and token handling proof
- sandbox isolation proof
- operator approval workflow
- policy enforcement proof
- audit and provenance proof
- rollback and incident plan
- dependency review

## No-Go Conditions

The work must stop if any of these appear before approval:

- runtime enabled
- external call path added
- credentials or tokens stored
- sandbox execution enabled
- activation enabled
- route registration enabled
- implementation approval set true without new ADR
- package or migration drift
- privileged bypass

## Decision

AION-115 approves checkpoint and evidence maintenance only. It blocks connector
implementation until a future ADR and gate package explicitly change scope.
