# Operator Role Model

## Roles

- `viewer`: read-only console access to redacted status and summaries.
- `operator`: viewer access plus governed dry-run request and preview access.
- `reviewer`: operator access plus review record creation.
- `admin`: reviewer access plus local design-time access to settings safety
  views and role provisioning proposals.
- `auditor`: read-only access to audit, provenance, policy, and redacted
  evidence summaries.
- `system_service`: internal service actor for local system events, never a
  human console shortcut.

## Permissions

Read permissions cover local, redacted console views. Dry-run permissions cover
request and preview records only. Review permissions cover review records only.

Allowed read actions include:

- view overview and readiness summaries,
- view release and lifecycle state,
- view module and provider hardening summaries,
- view notifications and incidents,
- view registry and audit summaries.

Allowed dry-run actions include:

- create governed operator action request,
- create dry-run preview,
- dismiss non-blocking finding with reason,
- export redacted summary.

Allowed review actions include:

- create review record,
- acknowledge blocked state,
- request changes,
- reject unsafe request,
- approve preview only.

## Forbidden Actions

Forbidden for every role in this phase:

- execute,
- activate,
- load code,
- register route,
- enable provider,
- store credentials,
- hard delete,
- bypass policy,
- bypass audit,
- reveal raw prompt,
- reveal hidden reasoning,
- reveal secret-like values.

## Escalation Rules

Role escalation must not be self-service. Future role changes require policy,
audit, and separation of duties. A reviewer should not be the sole approver of
their own high-risk request. Admin role use should be auditable and locally
bounded until production auth is designed.

## Separation Of Duties

Dry-run request creation, review, and audit inspection are separate concerns.
No role may convert a review into execution in AION-093.
