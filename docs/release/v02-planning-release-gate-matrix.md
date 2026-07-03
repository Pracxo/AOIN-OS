# v0.2 Planning Release Gate Matrix

| Area | Required gate | Required evidence | Expected safe state | Approval state | Release blocker if violated | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Planning charter | `./scripts/v02-planning-charter-check.sh` | `docs/release/v02-planning-charter.md` | Planning-only charter exists | false | yes | Root v0.2 planning baseline. |
| Planning stabilization | `./scripts/v02-planning-stabilization-gate.sh` | `docs/release/v02-planning-stabilization-gate.md` | Planning backlog remains blocked for implementation | false | yes | No runtime work approved. |
| Readiness final review | `./scripts/v02-readiness-final-review.sh` | `docs/release/v02-readiness-final-review.md` | Readiness final review passed | false | yes | Implementation guard remains locked. |
| Implementation kickoff boundary | `./scripts/v02-implementation-kickoff-boundary-check.sh` | `docs/release/v02-implementation-kickoff-boundary.md` | Future implementation request boundary only | false | yes | No kickoff execution. |
| Approval workflow | `./scripts/v02-approval-workflow-stabilization-gate.sh` | `docs/release/v02-approval-workflow-stabilization-gate.md` | No bypass or missing approval record | false | yes | Expiry, revocation, and dual-control remain required. |
| Workstream intake | `./scripts/v02-workstream-intake-readiness-gate.sh` | `docs/release/v02-workstream-intake-readiness-gate.md` | Workstream intake remains preview-only | false | yes | Queue readiness is not approval. |
| Preimplementation master freeze | `./scripts/v02-preimplementation-master-freeze.sh` | `docs/release/v02-preimplementation-master-freeze.md` | Implementation lock remains closed | false | yes | Final preimplementation freeze remains active. |
| Proposal registry | `./scripts/v02-workstream-proposal-registry-check.sh` | `docs/release/v02-workstream-proposal-registry.md` | Proposal registry remains preview-only | false | yes | Proposal implementation approval remains false. |
| Proposal registry stabilization | `./scripts/v02-proposal-registry-stabilization-gate.sh` | `docs/release/v02-proposal-registry-stabilization-gate.md` | Approval queue remains preview-only | false | yes | Candidate evidence does not approve execution. |
| Planning master checkpoint | `./scripts/v02-planning-master-checkpoint.sh` | `docs/release/v02-planning-master-checkpoint.md` | AION-119 through AION-128 evidence consolidated | false | yes | No v0.2 tag or release. |
| Final planning release gate | `./scripts/v02-final-planning-release-gate.sh` | `docs/release/v02-final-planning-release-gate.md` | Final planning gate passed | false | yes | AION-129 is not implementation. |
| Final planning freeze | `./scripts/v02-final-planning-freeze.sh` | `docs/release/v02-no-implementation-freeze.md` | Full repository check passed with no implementation approvals | false | yes | Direct execution remains strict. |
