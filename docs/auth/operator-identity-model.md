# Operator Identity Model

## Local Operator Identity

A local operator identity describes the operator context used by the console
design. It is synthetic in AION-093 and does not prove production identity.

Core fields:

- `actor_id`: stable local actor label, such as `local.operator`.
- `workspace_id`: local workspace label.
- `owner_scope`: policy scope list, such as `workspace:main`.
- `roles`: role labels assigned for local access design.

## Role Labels

Supported role labels are:

- `viewer`
- `operator`
- `reviewer`
- `admin`
- `auditor`
- `system_service`

## Identity Source Assumptions

In v0.1 and AION-093, ActorContext remains the current internal context
mechanism. Local examples are not account records. They are design fixtures
used to reason about permissions and console boundaries.

## Trust Boundaries

Local identity labels are not enough to bypass Brain policy. Every backend
action remains subject to policy decisions, audit, approval, autonomy, and
redaction rules. Local identity is input to governance, not a replacement for
governance.

## Synthetic Local Identities

Demo identities may represent local operators, reviewers, admins, auditors, or
system services. They must be clearly marked as synthetic. They must not
contain credentials or production identity claims.

## Future Identity Provider Requirements

Future production identity requires:

- a production identity provider design,
- role provisioning rules,
- account lifecycle rules,
- audit correlation,
- session binding,
- break-glass design,
- security review,
- release gate approval.
