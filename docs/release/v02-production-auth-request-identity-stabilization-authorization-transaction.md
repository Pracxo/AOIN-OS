# v0.2 Production Auth Request Identity Stabilization Authorization Transaction

Status: `approved`

## Purpose

AION-157 closes `AION-155-PA-0003` as consumed by AION-156 PR 66 and creates
`AION-157-PA-0004` as the single-use authorization for future AION-158 request
identity boundary stabilization. AION-157 changes no implementation source,
creates no runtime API route, and creates no v0.2 tag or release.

## Authorization Transaction

- `authorization_transaction_id=AION-157-PA-0004`
- `approval_record_id=AION-157-PA-0004`
- `parent_authorization_transaction_id=AION-155-PA-0003`
- `candidate_id=production-auth-request-identity-boundary-stabilization`
- `workstream=production-auth-request-integration-hardening`
- `implementation_task=AION-158`
- `authorization_scope=disabled-request-identity-boundary-stabilization`

## Approval State

- `authorization_transaction_approved=true`
- `explicit_approval_record_approval=true`
- `implementation_authorization_approved=true`
- `implementation_go_status=true`
- `implementation_no_go_status=false`

## Lifecycle

- `authorization_active=false`
- `authorization_consumed=true`
- `authorization_consumed_by_task=AION-158`
- `authorization_consumed_by_pr=68`
- `authorization_consumed_by_feature_commit=767fd9b228b00b04569df2e3b1b3f6bc9ecd846f`
- `authorization_consumed_by_merge_commit=f792c92e1d8a73ec8e7377b5d59269dea359006d`
- `authorization_expired=true`
- `authorization_reusable=false`
- Exactly one active production-auth authorization may exist.

## AION-158 Acceptance Contract

AION-158 may stabilize only the disabled request identity boundary. It may
replace the existing middleware internals with pure ASGI middleware, preserve
the public class name or provide a compatibility alias, preserve
RequestContextMiddleware ownership, prove middleware order, preserve streaming
responses and request bodies, propagate cancellation, handle disconnects
without identity state, bypass non-HTTP scopes, reject forged identity state,
prevent duplicate registration, preserve anonymous disabled identity, harden
state isolation, and add deterministic evidence, diagnostics, concurrency,
reentrancy, and performance-smoke coverage.

## Prohibited Scope

Identity verification, authenticated requests, authorization header parsing,
cookie parsing, credentials, passwords, tokens, sessions, identity providers,
external calls, auth endpoints, OpenAPI security, package files, lockfiles,
migrations, SDK or CLI runtime surfaces, connector runtime, operator writes,
module activation, sandbox execution, runtime guard release, v0.2 tags, and
v0.2 releases remain prohibited.

## Expiry

This authorization expires when AION-158 merges or when
`AION-157-PA-0004` is explicitly revoked.

## AION-158 Implementation Note

AION-158 implements the authorized stabilization scope with pure ASGI
middleware and disabled runtime guard checks. Formal lifecycle closeout for
`AION-157-PA-0004` remains deferred to AION-159 after merge.

## AION-159 Closeout

AION-159 marks this transaction consumed by AION-158 PR 68:
`authorization_active=false`, `authorization_consumed=true`,
`authorization_expired=true`, and `authorization_reusable=false`.
