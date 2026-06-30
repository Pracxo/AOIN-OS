# Post-v0.1 Release Candidate No-Go Conditions

## No-Go Checks

AION-118 fails if any check detects:

- v0.2 tag created
- connector runtime enabled
- operator write execution enabled
- production auth enabled
- module activation enabled
- external calls enabled
- credential storage enabled
- token storage enabled
- sandbox execution enabled
- package files added
- migrations added
- runtime API execution routes added
- implementation approval set true
- provider SDKs, connector SDK dependencies, or network clients added
- OAuth, OIDC, or SAML runtime enabled
- capability activation, code loading, or runtime registration enabled
- external model calls or external notifications enabled
- tool execution, action proposal execution, write path execution, or hard
  deletion enabled
- privileged bypass, policy bypass, or audit bypass added

## Allowed Evidence

Docs, examples, static demo data, and scripts may describe future v0.2 work
only as disabled, denied, no-go, future, or planning material. They must not
approve implementation or create runtime behavior.

## Regression Script

The no-go checks are enforced by:

```bash
./scripts/post-v01-release-candidate-no-go-regression.sh
```
