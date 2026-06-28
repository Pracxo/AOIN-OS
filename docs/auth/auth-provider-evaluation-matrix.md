# Auth Provider Evaluation Matrix

## Scoring Criteria

Scores use 1 to 5, where 5 is strongest for AION Operator Console suitability.

| Option | Security Boundary Clarity | Token Lifecycle | Session Lifecycle | Audit Correlation | Role Provisioning | Group Mapping | Revocation | MFA Support | Local Dev Parity | Deployment Complexity | Vendor Lock-In | Operational Burden | Console Suitability | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| OIDC provider | 5 | 5 | 4 | 5 | 4 | 5 | 4 | 5 | 4 | 3 | 3 | 3 | 5 | 55 |
| SAML provider | 4 | 3 | 3 | 4 | 4 | 4 | 3 | 4 | 2 | 3 | 3 | 4 | 3 | 44 |
| Reverse proxy auth | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 4 | 3 | 4 | 4 | 3 | 4 | 43 |
| Local enterprise SSO bridge | 3 | 3 | 3 | 4 | 4 | 4 | 3 | 4 | 2 | 2 | 2 | 2 | 3 | 39 |
| Passkey/WebAuthn future option | 5 | 4 | 4 | 4 | 2 | 2 | 4 | 5 | 2 | 2 | 4 | 3 | 3 | 44 |
| Dev-only local auth, not production | 1 | 1 | 1 | 3 | 2 | 1 | 1 | 1 | 5 | 5 | 5 | 5 | 1 | 32 |

## Recommended Direction

Recommend an OIDC-compatible production auth architecture as the future primary
path. It gives AION the clearest identity assertion model, best fit for modern
operator consoles, strong group/claim mapping support, and workable local
development parity through mock-only disabled prototypes.

Reverse proxy auth may be supported later as an optional deployment pattern.
It must not become a blind header-trust model.

## Risks

- token validation drift
- stale group mapping
- provider outage
- reverse proxy spoofing
- local development behavior diverges from production
- role mapping accidentally bypasses policy
- audit correlation misses provider subject references

## Mitigations

- central auth boundary with explicit validation contract
- signed or otherwise verifiable identity assertions
- fail-closed role mapping
- revocation test before release
- audit correlation test before release
- mock-only disabled prototype in AION-099
- release gate before any runtime provider integration
