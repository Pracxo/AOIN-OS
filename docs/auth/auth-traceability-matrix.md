# Auth Traceability Matrix

## Purpose

The traceability matrix maps the local auth prototype surfaces to the evidence
scripts that keep them disabled, mock-only, or read-only.

| Surface | Traceability | Evidence script |
| --- | --- | --- |
| Role | Role matrix filters visible static console sections only. | `./scripts/role-filter-check.sh` |
| Session | Local session preview carries synthetic context only. | `./scripts/local-session-check.sh` |
| Action authorization | Dry-run action authorization allows preview/review records only. | `./scripts/action-authorization-check.sh` |
| Policy | Policy remains authoritative for privileged decisions. | `./scripts/auth-design-check.sh` |
| Static console | Auth and session panels remain read-only and input-free. | `./scripts/static-console-safety-check.sh` |
| Audit | Local auth, session, role, action authorization, and auth runtime audits remain local. | `./scripts/auth-prototype-review.sh` |
| Forbidden action | Forbidden descriptors remain visible and disabled. | `./scripts/role-filter-check.sh` |

## Required Trace

Every future auth task must identify the affected role, session, action
authorization, policy, static console, audit, and forbidden-action surfaces.
If a surface would gain writes, execution, activation, provider calls,
production auth, credentials, protected material issuance, browser storage, or
external identity runtime, the gate must fail.
