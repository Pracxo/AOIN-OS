# Connector Runtime Review No-Go Pack

## Purpose

This no-go pack lists the AION-109 regression checks that must remain passed before any future connector implementation phase.

## No-Go Checks

| Check | Expected state | Evidence |
| --- | --- | --- |
| connector runtime enabled | absent | `./scripts/connector-runtime-no-external-call-regression.sh` |
| external call path added | absent | `./scripts/connector-runtime-no-external-call-regression.sh` |
| requests, httpx, or aiohttp connector runtime usage | absent | `./scripts/connector-runtime-no-external-call-regression.sh` |
| connector SDK dependency added | absent | `./scripts/connector-runtime-no-external-call-regression.sh` |
| credentials stored | absent | `./scripts/connector-runtime-no-external-call-regression.sh` |
| tokens stored | absent | `./scripts/connector-runtime-no-external-call-regression.sh` |
| dynamic route registration added | absent | `./scripts/connector-runtime-no-external-call-regression.sh` |
| connector activation enabled | absent | `./scripts/connector-runtime-no-external-call-regression.sh` |
| raw prompt egress allowed | absent | `./scripts/connector-runtime-no-external-call-regression.sh` |
| hidden reasoning egress allowed | absent | `./scripts/connector-runtime-no-external-call-regression.sh` |
| secret egress allowed | absent | `./scripts/connector-runtime-no-external-call-regression.sh` |
| policy bypass | absent | `./scripts/connector-runtime-no-external-call-regression.sh` |
| audit bypass | absent | `./scripts/connector-runtime-no-external-call-regression.sh` |

## Review Rule

Any failed no-go row blocks connector implementation. A failed row must be resolved with a follow-up design review before runtime work can proceed.
