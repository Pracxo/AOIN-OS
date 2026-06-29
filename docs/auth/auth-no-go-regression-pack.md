# Auth No-Go Regression Pack

## Purpose

The no-go regression pack lists the auth runtime additions that remain blocked
after AION-104.

## No-Go Checks

- Login route.
- Logout route.
- Token route.
- Callback route.
- Session storage.
- Cookie issuance.
- Password field.
- Token field.
- Credential field.
- Provider SDK.
- Package file.
- External identity call.
- Production auth enabled.
- Auth bypass.

## Expected Result

`./scripts/auth-no-go-regression.sh` must report all checks passed. Any failed
row is a release blocker and must be fixed forward without skipping, xfail, or
softening the no-go condition.

## Evidence

The sample result lives in
`examples/auth/auth-no-go-regression-result.json`. It is a static passed result
only and does not represent runtime auth state.
