# Platform Integration Risk Register

## Purpose

This register records cross-phase risks that remain release blockers for the
AION-117 post-v0.1 platform integration checkpoint.

| Risk | Blocked state | Evidence owner | Release blocker |
| --- | --- | --- | --- |
| Operator approval bypass | No operator write execution is approved | Operator platform gates | Yes |
| Connector policy bypass | Connector allow paths remain denied | Connector policy and release gates | Yes |
| Production auth bypass | Production auth runtime remains disabled | Auth prototype and auth no-go gates | Yes |
| Connector credential exfiltration | Credential storage and values are absent | Connector credential gates | Yes |
| External call leakage | External network clients and provider calls are absent | Connector release and platform no-go gates | Yes |
| Sandbox escape | Sandbox execution remains disabled | Connector sandbox gates | Yes |
| Module activation bypass | Code loading, runtime registration, and activation are absent | Module activation gates | Yes |
| Runtime route registration drift | API execution routes are absent | Platform no-go gate | Yes |
| Audit/provenance gaps | Evidence rows must remain traceable to local scripts | Cross-phase evidence pack | Yes |
| Static console misrepresentation | Static UI must show preview-only safe state | Static console safety and UX gates | Yes |
| Package dependency drift | Package and lock files are absent | Platform no-go gate | Yes |
| Migration drift | Database migrations are absent | Platform no-go gate | Yes |

## Triage rule

Fix the first failing gate, rerun the narrow no-go regression, then rerun the
platform integration checkpoint and freeze check. Do not skip or soften a
release blocker.
