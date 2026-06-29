# Auth Runtime Disabled Proof

## Proof Statement

AION-104 proves the auth runtime remains disabled after the local prototype
review. The disabled proof is evidence-only and does not add runtime auth.

## Required False Flags

- `production_auth_enabled=false`
- `auth_runtime_enabled=false`
- `credentials_enabled=false`
- `token_issuance_enabled=false`
- `cookie_issuance_enabled=false`
- `session_persistence_enabled=false`
- `login_endpoint_enabled=false`
- `logout_endpoint_enabled=false`
- `external_identity_provider_enabled=false`

## Runtime Absence Proof

- No provider SDK dependency is added.
- No package file or lockfile is added.
- No migration is added.
- No login, logout, callback, token, or provider route is added.
- No real token, cookie, session, credential, password, or provider value is
  accepted, generated, stored, or rendered.

## Static Console Proof

The static console may display disabled status and mock claims preview evidence
only. It has no form, input, browser storage, write verb, provider call, login
control, logout control, credential control, token control, cookie control, or
session persistence control.

## Evidence Files

- `examples/auth/auth-runtime-disabled-proof.json`
- `examples/auth/auth-no-go-regression-result.json`
- `./scripts/auth-runtime-check.sh`
- `./scripts/auth-no-go-regression.sh`
