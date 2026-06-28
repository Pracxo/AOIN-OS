# Operator Console No-Go Conditions

AION-087 does not build a UI. A future UI milestone is blocked if any no-go
condition remains unresolved.

## No-go conditions for building UI

- unresolved release blockers
- failing RC gate
- failing freeze gate
- activation toggle enabled
- code loading enabled
- external calls enabled by default
- raw prompt exposure risk
- secret display risk
- policy bypass risk
- missing audit trail
- module lifecycle states unclear
- provider readiness states unclear
- no stable API contract
- no data redaction policy

## Decision rule

Any no-go condition blocks runtime UI implementation. The next acceptable step
is a contract, docs, or dry-run validation task that removes the blocker
without creating a privileged UI path.

## AION-100 UI release no-go conditions

The static UI release gate also blocks frontend dependencies, build tools,
external scripts, non-local fetch targets, write verbs, activation controls,
execution controls, provider-call controls, login forms, credential fields,
token/cookie/session storage, protected output display, and production UI
claims.
