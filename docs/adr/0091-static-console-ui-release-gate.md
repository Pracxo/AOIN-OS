# 0091: Static Console UI Release Gate

## Status

Accepted.

## Context

AION-089 through AION-099 created a local static Operator Console and several
read-only safety panels. Before future UI, auth, or runtime work can proceed,
AION needs a stable checkpoint proving the static console remains safe.

## Decision

Add a static console UI release gate.

The static console remains dependency-free and read-only.

No write, activation, execution, provider, login, credential, token, cookie, or
session controls are allowed.

The UI release gate becomes mandatory before future UI work.

## Reason

AION needs a stable operator platform checkpoint before progressing to auth or
runtime UI implementation.

## Consequences

Future UI work must pass static safety gates. A failed static gate blocks UI
release until the console returns to local-only, dependency-free, read-only
behavior.

## Constraints

- no frontend dependencies
- no production UI claim
- no privileged bypass
- no external calls
- no production auth
- no provider runtime
- no activation
- no execution
