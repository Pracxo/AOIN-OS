# v0.2 Decision Package Evidence Matrix

| Evidence item | File or command | Required state |
| --- | --- | --- |
| Decision package preview | `docs/release/v02-decision-package-preview.md` | present |
| Approval readiness evidence bundle | `docs/release/v02-approval-readiness-evidence-bundle.md` | present |
| Runtime decision boundary | `docs/release/v02-runtime-decision-boundary.md` | present |
| Decision package state model | `docs/release/v02-decision-package-state-model.md` | present |
| No-go register | `docs/release/v02-decision-package-no-go.md` | present |
| Closeout checklist | `docs/release/v02-decision-package-checklist.md` | present |
| ADR | `docs/adr/0129-v02-decision-package-preview.md` | indexed |
| Examples | `examples/release/v02-decision-package-preview.json` | valid JSON |
| Static console data | `operator-console-static/demo-data/v02-decision-package-preview.json` | read-only |
| Preview gate | `./scripts/v02-decision-package-preview-check.sh` | passing |
| Freeze gate | `./scripts/v02-decision-package-freeze.sh` | passing |
| No-go regression | `./scripts/v02-decision-package-no-go-regression.sh` | passing |
| Test coverage | `services/brain-api/tests/test_v02_decision_package_preview_docs.py` | passing |

## Evidence Rule

Every evidence item is advisory until a future approval workflow creates an
explicit decision record. Missing evidence blocks future approval consideration.
Complete evidence still keeps implementation approval false.
