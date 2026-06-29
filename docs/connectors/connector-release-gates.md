# Connector Release Gates

## Purpose

Connector release gates define the evidence required before future connector
implementation work can advance. AION-106 keeps all runtime behavior disabled.

## Required Gates

| Gate | Expected evidence | Release blocker |
| --- | --- | --- |
| threat model approved | `docs/connectors/connector-threat-model.md` | yes |
| credential boundary approved | `docs/connectors/connector-credential-boundary.md` | yes |
| egress guard approved | `docs/connectors/connector-egress-guard.md` | yes |
| ingress guard approved | `docs/connectors/connector-ingress-guard.md` | yes |
| policy model approved | `docs/policy-model.md` connector policy section | yes |
| action authorization integration tested | dry-run action authorization evidence | yes |
| audit/provenance tested | connector audit/provenance design evidence | yes |
| operator review tested | operator review gate evidence | yes |
| sandbox requirements approved | connector sandbox posture in manifest design | yes |
| disabled-by-default prototype green | future disabled prototype check | yes |
| release/freeze gate green | `./scripts/connector-boundary-design-check.sh` | yes |

## Local Gate Commands

```bash
./scripts/connector-boundary-design-check.sh
./scripts/connector-no-go-regression.sh
./scripts/docs-check.sh
./scripts/final-docs-audit.sh
./scripts/verify-no-domain-drift.sh
./scripts/boundary-check.sh
```

## Gate Decision

Future connector work must fail closed if any gate is missing, if external calls
are enabled by default, if credentials or tokens are present, if connector SDK
dependencies appear before review, or if policy/action authorization/audit can
be bypassed.
## AION-108 Disabled Prototype Relationship

The disabled connector prototype adds `scripts/connector-runtime-check.sh` as a
local release-gate input. Passing the gate proves runtime, external calls,
credentials, token storage, activation, and route registration remain disabled.

## AION-109 Review Gate Relationship

AION-109 adds `scripts/connector-runtime-review.sh` and
`scripts/connector-runtime-no-external-call-regression.sh` as release-gate
inputs. Future connector tasks must keep these gates green before any runtime
implementation is considered.
