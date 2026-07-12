# ADR 0142: v0.2 Production Auth Implementation Authorization

## Context

AION-150 completed the v0.2 authorization governance baseline while keeping all
runtime and implementation approvals false. AION-151 is the first scoped
authorization transaction after that closeout.

## Decision

Authorize the scoped production-auth core implementation for AION-152. Set the
canonical scoped authorization transaction `AION-151-PA-0001` to approved. Keep
runtime implementation unapproved. Keep production-auth runtime disabled. Keep
runtime enablement guards locked. Keep credentials, tokens, sessions, providers,
endpoints, migrations, packages, and external calls prohibited. Permit no other
workstream authorization. Create no v0.2 tag or release.

## Scope

The approved candidate is `production-auth-core`, the workstream is
`production-auth-implementation`, the implementation task is `AION-152`, and the
authorization scope is `disabled-production-auth-core`.

## Alternatives

One alternative was to keep all implementation authorization false until runtime
auth could be implemented in one step. That would obscure review boundaries.
Another was to approve production-auth runtime directly. That is rejected
because runtime guards remain locked.

## Security impact

The decision permits only disabled internal core work. It prohibits runtime
identity providers, endpoints, credentials, passwords, token issuance, token
storage, sessions, cookies, external calls, provider SDKs, migrations, package
changes, operator writes, connector runtime, module activation, and sandbox
execution.

## Runtime impact

Runtime impact is none. `runtime_implementation_approved=false`,
`production_auth_runtime_enabled=false`, and `runtime_no_go_status=true`.

## Approval transaction

`authorization_transaction_id=AION-151-PA-0001`.
`approval_record_id=AION-151-PA-0001`.
`authorization_transaction_approved=true`.
`explicit_approval_record_approval=true`.
`implementation_authorization_approved=true`.
`implementation_go_status=true`.
`implementation_no_go_status=false`.

## Guard hold

All runtime guard release approvals remain false, and the runtime guard hold
stays active until a later explicit approval transaction changes it.

## Expiry

The authorization expires when AION-152 is merged or the record is explicitly
revoked.

## Revocation

Revocation requires a follow-up approval record that names
`AION-151-PA-0001`, records reviewer roles, and keeps runtime guard releases
false.

## Consequences

AION-152 can begin only within the disabled production-auth core scope. Any
runtime enablement or broader candidate approval requires a separate future
authorization transaction.

## Future AION-152 requirements

AION-152 must include focused tests, audit/provenance evidence, redacted
diagnostics, disabled-by-default configuration, and read-only static-console
evidence. It must not create a v0.2 tag or release.
