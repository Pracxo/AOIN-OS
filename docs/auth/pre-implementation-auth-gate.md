# Pre-Implementation Auth Gate

## Purpose

This gate defines what must be true before any AION-105 or later auth
implementation task can move beyond docs, design, and evidence planning.

## Must Be True Before AION-105+

- `./scripts/auth-prototype-review.sh` passes.
- `./scripts/auth-no-go-regression.sh` passes.
- `./scripts/operator-platform-regression.sh` passes on the candidate branch.
- CI is green on the branch.
- A new ADR explicitly approves the implementation class and threat model.
- Production auth, protected material lifecycle, provider integration, browser
  session lifecycle, migrations, and rollback path are documented before code.

## Gate Fail Conditions

The gate fails if the branch adds login/logout, credentials, token issuance,
cookie issuance, persisted sessions, external identity runtime, provider SDKs,
package files, build tooling, migrations, API routers, writes, activation,
execution, hard delete, external calls, or privileged bypass without a specific
approved implementation ADR.

## Required Scripts

```bash
./scripts/auth-prototype-review.sh
./scripts/auth-no-go-regression.sh
./scripts/auth-runtime-check.sh
./scripts/production-auth-architecture-check.sh
./scripts/local-auth-check.sh
./scripts/local-session-check.sh
./scripts/role-filter-check.sh
./scripts/action-authorization-check.sh
./scripts/ui-release-gate.sh
```

## Required CI State

All required GitHub checks must be green. Local-only success is not sufficient
for implementation work.

## Required ADR State

ADR 0095 keeps auth disabled/mock-only. Any implementation phase needs a later
ADR that supersedes only the specific boundary it is approved to change.

## Rollback Path

If a future branch fails this gate, remove the runtime or dependency addition,
restore the disabled/mock-only boundary, rerun the narrow failing script, and
then rerun the review and no-go regression scripts.

## Next Approved Work Types

Allowed next work types are design review, threat model refinement, connector
boundary review, credential lifecycle design, migration design, CI gate design,
and rollback design. Runtime auth remains blocked until a later ADR changes
that boundary.

## AION-117 Platform Integration Requirement

AION-117 adds `./scripts/platform-integration-checkpoint.sh`,
`./scripts/platform-integration-freeze-check.sh`, and
`./scripts/platform-integration-no-go-regression.sh` as required cross-phase
evidence before any production auth implementation ADR can be reviewed.
Production auth, login/logout behavior, session persistence, credential
storage, token storage, external identity runtime, package files, migrations,
and API runtime execution routes remain blocked.

## AION-119 Planning Charter Requirement

AION-119 adds the v0.2 planning charter as an additional prerequisite before
production auth implementation can be proposed. Planning may define an ADR,
gate, rollback, audit/provenance, operator review, and security review model,
but production auth runtime, credentials, tokens, sessions, external identity
runtime, package files, migrations, and runtime API routes remain blocked.

## AION-120 Planning Stabilization Dependency

AION-120 adds the v0.2 planning stabilization gate and backlog governance
freeze as additional prerequisites before production auth implementation can be
proposed. Production auth, credential storage, token storage, session
persistence, external identity runtime, migrations, package files, and runtime
API routes remain blocked.

## AION-121 Readiness Final Review Dependency

AION-121 adds the v0.2 readiness final review as an additional prerequisite
before production auth implementation can be proposed. Production auth,
credential storage, token storage, session persistence, external identity
runtime, migrations, package files, and runtime API routes remain blocked until
future scoped ADR, gate, security, rollback, audit/provenance, operator review,
and no-go evidence pass.

## AION-122 Implementation Kickoff Boundary Dependency

AION-122 adds the v0.2 implementation kickoff boundary as an additional
prerequisite before production auth implementation can be proposed. Production
auth, credential storage, token storage, session persistence, external identity
runtime, migrations, package files, runtime API routes, approval workflow
bypass, ADR dependency bypass, and gate dependency bypass remain blocked until
future scoped request, approval decision record, ADR, gate, security, rollback,
audit/provenance, operator review, and no-go evidence pass.

## AION-124 Workstream Intake Readiness Dependency

AION-124 adds the v0.2 workstream intake readiness gate as an additional
prerequisite before production auth implementation can be proposed. Production
auth, credential storage, token storage, session persistence, external identity
runtime, migrations, package files, runtime API routes, workstream
implementation approval, approval record missing, approval workflow bypass, ADR
dependency bypass, and gate dependency bypass remain blocked until future
scoped intake, approval record, ADR, gate, security, rollback,
audit/provenance, operator review, sequencing, and no-go evidence pass.
AION-125 keeps production auth behind the pre-implementation master freeze.
Production auth approval and runtime enablement remain false, and future auth
implementation still requires approval records, ADR evidence, release gate
evidence, no-go regression evidence, and full verification.

AION-126 indexes production auth implementation as a future proposal only.
Production auth approval, runtime auth enablement, external identity runtime,
credential storage, token storage, approval queue item approval, v0.2 tag
creation, and v0.2 release creation remain false or absent until a later
scoped approval task changes the boundary.

AION-127 keeps production auth implementation in the stabilized proposal
registry only. Production auth proposal implementation approval, approval
queue item approval, runtime auth enablement, external identity runtime,
credential storage, token storage, approval workflow bypass, approval record
missing, v0.2 tag creation, and v0.2 release creation remain false or absent
until a later scoped approval task changes the boundary.

AION-128 keeps production auth implementation inside the planning master
checkpoint only. Production auth proposal implementation approval, approval
queue item approval, production auth approval, runtime auth enablement,
external identity runtime, credential storage, token storage, approval
workflow bypass, approval record missing, v0.2 tag creation, and v0.2 release
creation remain false or absent until a later scoped approval task changes the
boundary.

## AION-129 Final Planning Release Gate

AION-129 keeps production auth implementation unapproved. OAuth/OIDC/SAML
runtime, external identity runtime, credential storage, token storage, login,
logout, session persistence, v0.2 tag creation, and v0.2 release creation
remain false or absent.

## AION-130 Planning Track Closeout

AION-130 keeps production auth implementation unapproved in the governance
handoff pack. OAuth/OIDC/SAML runtime, external identity runtime, credential
storage, token storage, login, logout, session persistence, v0.2 tag creation,
and v0.2 release creation remain false or absent.

## AION-131 Implementation Request Pack

AION-131 adds production auth implementation request templates only.
Production auth implementation remains unapproved. OAuth/OIDC/SAML runtime,
external identity runtime, credential storage, token storage, login, logout,
session persistence, v0.2 tag creation, and v0.2 release creation remain
false or absent.

## AION-132 Request Pack Stabilization

AION-132 adds production auth request evidence completeness and submission
freeze checks only. Production auth implementation remains unapproved.
OAuth/OIDC/SAML runtime, external identity runtime, credential storage, token
storage, login, logout, session persistence, v0.2 tag creation, and v0.2
release creation remain false or absent.

## AION-134 Submission Registry Preview

AION-134 catalogs the production auth implementation candidate as a submission
registry preview record only. Production auth implementation remains
unapproved. OAuth/OIDC/SAML runtime, external identity runtime, credential
storage, token storage, login, logout, session persistence, v0.2 tag creation,
and v0.2 release creation remain false or absent.

## AION-133 Request Pack Final Review

AION-133 adds production auth request final review and pre-approval submission
evidence only. Production auth implementation remains unapproved.
OAuth/OIDC/SAML runtime, external identity runtime, credential storage, token
storage, login, logout, session persistence, v0.2 tag creation, and v0.2
release creation remain false or absent.

## AION-135 Submission Registry Stabilization Boundary

AION-135 may list production auth as a future request candidate, but it does
not approve production auth implementation and does not enable production auth
runtime. Login endpoints, logout endpoints, session persistence, cookie
issuance, token issuance, external identity provider runtime,
OAuth/OIDC/SAML runtime, credential storage, and token storage remain disabled
or absent.

AION-136 may route production auth candidates to future reviewers, but routing
is not approval. Production auth implementation approval remains false, review
board decision approval remains false, and login/logout endpoints, session
persistence, cookie issuance, token issuance, external identity provider
runtime, OAuth/OIDC/SAML runtime, credential storage, and token storage remain
disabled or absent.

## AION-141 Approval Docket Boundary
Approval docket preview does not approve production auth implementation. Production auth runtime, login endpoints, logout endpoints, session persistence, cookie issuance, token issuance, external identity provider runtime, OAuth/OIDC/SAML runtime, credential storage, token storage, approval docket item approval, implementation decision record approval, runtime approval review approval, and runtime implementation approval remain disabled, absent, or false.

AION-137 may stabilize production auth review routing as future
decision-readiness evidence, but stabilization is not approval. Production auth
implementation approval remains false, routing decision approval remains false,
reviewer sign-off implementation approval remains false, and login/logout
endpoints, session persistence, cookie issuance, token issuance, external
identity provider runtime, OAuth/OIDC/SAML runtime, credential storage, and
token storage remain disabled or absent.

AION-138 may include production auth in the decision package preview, but
package completeness is not approval. Decision package approval remains false,
approval readiness approved remains false, production auth implementation
approval remains false, and login/logout endpoints, session persistence,
cookie issuance, token issuance, external identity provider runtime,
OAuth/OIDC/SAML runtime, credential storage, and token storage remain disabled
or absent.

AION-139 stabilizes production auth candidate evidence in the decision package
baseline only. Runtime decision readiness approval remains false, production
auth implementation approval remains false, and login/logout endpoints,
session persistence, cookie issuance, token issuance, external identity
provider runtime, OAuth/OIDC/SAML runtime, credential storage, and token
storage remain disabled or absent.

AION-140 finalizes production auth candidate evidence in the decision package
final review only. Runtime decision lock release approval remains false,
runtime decision readiness approval remains false, production auth
implementation approval remains false, and login/logout endpoints, session
persistence, cookie issuance, token issuance, external identity provider
runtime, OAuth/OIDC/SAML runtime, credential storage, and token storage remain
disabled or absent.

## AION-142 Approval Docket Stabilization Boundary
Approval docket stabilization does not approve production auth implementation. Production auth runtime, login endpoints, logout endpoints, session persistence, cookie issuance, token issuance, external identity provider runtime, OAuth/OIDC/SAML runtime, credential storage, token storage, approval docket stabilization approval, approval docket item approval, implementation decision record freeze approval, implementation decision record approval, runtime approval review approval, and runtime implementation approval remain disabled, absent, or false.
