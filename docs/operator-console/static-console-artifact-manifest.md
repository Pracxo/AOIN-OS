# Static Console Artifact Manifest

## Static files

- `operator-console-static/index.html`
- `operator-console-static/styles.css`
- `operator-console-static/app.js`
- `operator-console-static/README.md`

## Demo data files

- `operator-console-static/demo-data/overview-view-model.json`
- `operator-console-static/demo-data/module-lifecycle-view-model.json`
- `operator-console-static/demo-data/provider-hardening-view-model.json`
- `operator-console-static/demo-data/release-readiness-view-model.json`
- `operator-console-static/demo-data/incidents-view-model.json`
- `operator-console-static/demo-data/settings-safety-view-model.json`
- `operator-console-static/demo-data/module-lifecycle-dashboard.json`
- `operator-console-static/demo-data/generic-knowledge-trail.json`
- `operator-console-static/demo-data/module-activation-blockers.json`
- `operator-console-static/demo-data/module-mock-runtime-trail.json`
- `operator-console-static/demo-data/module-review-checklist.json`
- `operator-console-static/demo-data/operator-action-preview.json`
- `operator-console-static/demo-data/operator-action-blockers.json`
- `operator-console-static/demo-data/operator-action-review.json`
- `operator-console-static/demo-data/action-authorization-preview.json`
- `operator-console-static/demo-data/action-authorization-deny-matrix.json`
- `operator-console-static/demo-data/local-auth-status.json`
- `operator-console-static/demo-data/local-session-status.json`
- `operator-console-static/demo-data/local-session-preview.json`
- `operator-console-static/demo-data/role-access-matrix.json`
- `operator-console-static/demo-data/role-viewer-dashboard.json`
- `operator-console-static/demo-data/role-operator-dashboard.json`
- `operator-console-static/demo-data/role-reviewer-dashboard.json`
- `operator-console-static/demo-data/role-admin-dashboard.json`
- `operator-console-static/demo-data/role-auditor-dashboard.json`
- `operator-console-static/demo-data/auth-runtime-status.json`
- `operator-console-static/demo-data/mock-claims-preview.json`

## Scripts

- `scripts/static-console-safety-check.sh`
- `scripts/ui-release-gate.sh`
- `scripts/operator-console-static-check.sh`
- `scripts/operator-console-static-demo.sh`
- `scripts/module-lifecycle-dashboard-check.sh`
- `scripts/provider-dashboard-check.sh`
- `scripts/operator-actions-check.sh`
- `scripts/local-auth-check.sh`
- `scripts/local-session-check.sh`
- `scripts/role-filter-check.sh`
- `scripts/action-authorization-check.sh`
- `scripts/auth-runtime-check.sh`

## Docs

- `docs/operator-console/ui-release-gate.md`
- `docs/operator-console/static-console-safety-matrix.md`
- `docs/operator-console/operator-platform-checkpoint.md`
- `docs/operator-console/post-v0.1-ui-no-go-conditions.md`
- `docs/operator-console/static-console-artifact-manifest.md`
- `docs/operator-console/ui-release-evidence-summary.md`
- `docs/adr/0091-static-console-ui-release-gate.md`

## Tests

- `services/brain-api/tests/test_static_console_ui_release_gate.py`

## Expected safety boundaries

The static console must remain local-only, read-only, dependency-free, build
free, provider-call free, login free, credential free, token free, cookie free,
session-persistence free, activation free, execution free, and protected-output
free.
