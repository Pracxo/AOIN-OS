# Connector Implementation Readiness Decision

## Decision

Connector implementation is not approved yet.

## Current State

Connector runtime remains disabled. External calls remain absent. Credential and
token storage remain absent. Sandbox execution remains absent. Connector
activation and route registration remain absent.

## Future Approval Requirements

Future connector implementation requires:

- an explicit new ADR approving implementation scope
- a production auth decision
- credential store implementation approval
- sandbox implementation approval
- external call release gate evidence
- rollback design
- audit and provenance design
- no-go regression updates that prove unsafe paths stay denied by default

## Release Gate Result

AION-114 approves only the connector release gate and safety freeze. It does not
approve runtime execution, network access, credential storage, sandbox
execution, activation, route registration, provider SDK dependencies, or
production auth.
