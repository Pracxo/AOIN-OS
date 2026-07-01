# v0.2 Readiness Evidence Matrix

| Area | Evidence source | Gate script | Expected safe value | Approval status | Release blocker if violated | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| planning charter | `docs/release/v02-planning-charter.md` | `./scripts/v02-planning-charter-check.sh` | present | planning-only | yes | AION-119 remains the entry charter. |
| planning stabilization | `docs/release/v02-planning-stabilization-gate.md` | `./scripts/v02-planning-stabilization-gate.sh` | passed | planning-only | yes | AION-120 remains required. |
| implementation guard | `docs/release/v02-implementation-approval-guard.md` | `./scripts/v02-readiness-final-review.sh` | all approval values false | unapproved | yes | No readiness artifact grants implementation. |
| backlog governance | `docs/release/v02-backlog-governance-freeze.md` | `./scripts/v02-planning-freeze-check.sh` | backlog implementation unapproved | unapproved | yes | Intake is planning-only. |
| blocked work | `docs/release/v02-blocked-implementation-summary.md` | `./scripts/v02-readiness-final-no-go-regression.sh` | blocked list complete | unapproved | yes | Every runtime area needs a future ADR. |
| static console evidence | `operator-console-static/demo-data/v02-readiness-final-review.json` | `./scripts/static-console-ux-check.sh` | read-only bundled data | unapproved | yes | No input, write, release, or activation controls. |
| release boundary | `docs/release/v02-final-no-go-review.md` | `./scripts/v02-readiness-final-freeze.sh` | no tag and no release | unapproved | yes | `aion-v0.1.0` remains untouched. |
| repository boundary | `docs/release/v02-readiness-final-checklist.md` | `./scripts/check.sh` | no package, migration, API, SDK, or CLI drift | unapproved | yes | Full repository checks remain required. |
