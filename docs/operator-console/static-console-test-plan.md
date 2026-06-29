# Static Console Test Plan

## Required Tests

- static files exist
- no package files
- no external URLs
- app blocks non-localhost API
- app redacts sensitive fields
- demo JSON valid
- offline mode works
- read-only banner present
- activation controls absent
- forbidden action descriptors visible

## Script Coverage

`./scripts/operator-console-static-check.sh` verifies the static file contract,
demo JSON shape, redaction list, localhost guard, absence of write methods, and
absence of frontend build artifacts.

`./scripts/static-console-safety-check.sh` verifies the narrower static-only UI
release boundary: no external scripts, no CSS imports, no non-local fetch
targets, no write verbs, no credential inputs, redaction keys, demo fallback,
and no production UI claim.

`./scripts/ui-release-gate.sh` composes the static console, module lifecycle,
provider dashboard, operator action, local auth, local session, role filter,
action authorization, auth runtime, and static safety checks into one UI
release checkpoint.

`./scripts/operator-console-static-demo.sh --offline-ok --skip-api` verifies the
offline demo path without calling the API.

## Python Regression Coverage

`services/brain-api/tests/test_operator_console_static_prototype.py` verifies
the same boundary from the Brain API test suite. It intentionally inspects
static artifacts only and does not start a frontend server.

`services/brain-api/tests/test_static_console_ux_refinement.py` verifies the
AION-103 UX refinement docs, examples, skip link, navigation groups, safe
command allowlist, focus styles, localhost guard, and no-write JavaScript
boundary.

## UX Refinement Coverage

`./scripts/static-console-ux-check.sh` verifies:

- AION-103 docs and ADR 0094 are present and indexed.
- Navigation and accessibility examples are valid JSON.
- The skip link and navigation groups exist.
- Required safety banners remain visible.
- Safe command copy is restricted to approved local checks.
- `app.js` keeps the localhost guard, redaction path, no write verbs, no
  browser storage, and no external URL fetch.
- `styles.css` keeps focus styles and no external imports.
- Package files and frontend build tooling remain absent.

## Manual Smoke

```bash
python3 -m http.server 8090 --directory operator-console-static
open http://localhost:8090
open "http://localhost:8090?api=http://localhost:8080"
```

The page should show the visible banner:

`AION Operator Console Prototype — local, read-only, no activation`

When the API is unavailable, the status strip should report local API fallback
and the demo panels should render.
