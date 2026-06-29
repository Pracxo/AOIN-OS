# Connector No-Go Regression Pack

## Purpose

The connector no-go regression pack defines the checks that must stay green
before any future connector runtime can be proposed.

## No-Go Checks

- connector runtime added without gate
- network call added
- SDK dependency added
- credentials added
- token storage added
- dynamic route added
- connector activation enabled
- external calls enabled by default
- raw prompt egress allowed
- hidden reasoning egress allowed
- secret egress allowed
- policy bypass
- audit bypass

## Expected Result

Every no-go check must pass by proving the unsafe behavior is absent. Passing
the no-go regression does not approve connector runtime; it only proves the
repository still has no connector runtime, no external calls, no credentials,
no tokens, and no connector SDK dependency.

## Local Command

```bash
./scripts/connector-no-go-regression.sh
```

Expected result:

```text
Connector no-go regression PASS
```
## AION-108 Disabled Prototype Relationship

The no-go regression pack now allows the scoped AION-108 disabled connector
prototype files while continuing to block network clients, external service
calls, connector/provider SDKs, credentials, token storage, route registration,
activation, and execution paths.
