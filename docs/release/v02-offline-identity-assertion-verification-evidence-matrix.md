# v0.2 Offline Identity Assertion Verification Evidence Matrix

Task: AION-161

| Evidence | Required value | Gate |
| --- | --- | --- |
| AION-159 lifecycle | inactive, consumed by AION-160 PR 70, expired, non-reusable | validator and closeout JSON |
| AION-161 lifecycle | active, unconsumed, unexpired, non-reusable | validator and authorization JSON |
| Active authorizations | exactly one, `AION-161-PA-0006` | no-go regression |
| Dependency | `cryptography>=49.0.0,<50.0.0` in `services/brain-api/pyproject.toml` only for AION-162 | validator |
| Fixed algorithm | Ed25519 only | scope and threat model |
| Domain separation | `AION-IDENTITY-ASSERTION-V1` plus canonical JSON | scope and ADR |
| Runtime auth | false | runtime hold |
| ActorContext application | false | runtime hold |
| RequestIdentityContext application | false | runtime hold |
| Runtime private key | false | runtime hold |
| Provider networking | false | no-go regression |
| Replay cache | false; replay protection required later | no-go regression |
| v0.2 release | absent | no-go regression |

Required commands:

- `./scripts/v02-offline-identity-assertion-verification-authorization-no-go-regression.sh`
- `./scripts/v02-offline-identity-assertion-verification-authorization-check.sh`
- inherited production-auth actor-context and request-identity gates
