# v0.2 Workstream Rejection Rules

## Purpose

These rules reject candidate workstreams before planning if required evidence or boundary constraints are missing.

## Rejection Conditions

- missing problem statement
- missing risk statement
- missing ADR dependency
- missing gate dependency
- missing rollback/audit consideration
- missing security review
- runtime enablement requested without ADR
- external call requested without release gate
- credential/token storage requested without credential store ADR
- sandbox execution requested without sandbox runtime ADR
- implementation approval requested directly
- package/migration/runtime route requested prematurely

## Result

Rejected workstreams remain unapproved. The reviewer records the rejected condition, the missing evidence, and the next planning action. No runtime, external call, credential/token, sandbox, package, migration, or runtime route change is allowed.
AION-125 preserves these rejection rules as master-freeze policy. Future
workstream proposals that bypass problem, risk, ADR, gate, rollback/audit,
security, architecture, operator, approval record, or no-go evidence remain
rejected before implementation.
