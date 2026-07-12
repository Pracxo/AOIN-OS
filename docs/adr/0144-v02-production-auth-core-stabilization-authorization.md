# 0144: v0.2 Production Auth Core Stabilization Authorization

Status: Accepted

## Context

AION-152 merged the disabled production-auth core implementation and consumed
the scoped AION-151 authorization transaction. The next implementation task
needs a separate authorization because `AION-151-PA-0001` is historical,
expired, consumed, and non-reusable.

## Decision

AION-153 creates `authorization_transaction_id=AION-153-PA-0002` and
`approval_record_id=AION-153-PA-0002` for the future AION-154
`disabled-production-auth-core-stabilization` task.

The transaction references
`parent_authorization_transaction_id=AION-151-PA-0001`, but does not reuse the
parent. AION-153 keeps `authorization_active=true`,
`authorization_consumed=false`, `authorization_expired=false`, and
`authorization_reusable=false` for the new transaction.

## Consequences

AION-154 may later modify internal disabled production-auth core code only
within the stabilization scope. AION-153 itself remains governance-only and
does not modify runtime implementation code.

Runtime auth remains disabled. Endpoint, storage, provider, network, package,
migration, SDK, CLI, operator, connector, module, sandbox, tag, and release
surfaces remain blocked.

## Verification

- `./scripts/v02-production-auth-stabilization-authorization-check.sh`
- `./scripts/v02-production-auth-stabilization-runtime-guard-hold.sh`
- `./scripts/v02-production-auth-stabilization-authorization-no-go-regression.sh`
