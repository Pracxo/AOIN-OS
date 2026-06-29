# Operator Platform Regression Evidence

The AION-102 evidence pack records the long-running regression matrix and
freeze gate outputs. All rows are release blockers when failed.

| Evidence area | Scripts run | Expected status | Blocker if failed | Notes |
| --- | --- | --- | --- | --- |
| Static console safety | `./scripts/static-console-safety-check.sh` | passed | Yes | Confirms local-only, read-only, no frontend dependency, no build step, no login, no provider-call controls, and no protected-output rendering. |
| UI release gate | `./scripts/ui-release-gate.sh` | passed | Yes | Reuses the AION-100 release gate. |
| Operator checkpoint | `./scripts/operator-platform-checkpoint.sh` | passed | Yes | Reuses the AION-101 checkpoint evidence pack. |
| Module lifecycle dashboard | `./scripts/module-lifecycle-dashboard-check.sh` | passed | Yes | Keeps activation and execution blocked. |
| Provider hardening dashboard | `./scripts/provider-dashboard-check.sh` | passed | Yes | Keeps provider calls and external model calls absent. |
| Operator actions | `./scripts/operator-actions-check.sh` | passed | Yes | Keeps action proposals and operator actions dry-run only. |
| Action authorization | `./scripts/action-authorization-check.sh` | passed | Yes | Keeps policy decisions dry-run and fail-closed. |
| Auth safety | `./scripts/production-auth-architecture-check.sh` and `./scripts/auth-runtime-check.sh` | passed | Yes | Keeps production auth architecture design-only and disabled auth runtime hard-off. |
| Local auth and session | `./scripts/local-auth-check.sh` and `./scripts/local-session-check.sh` | passed | Yes | Keeps identity and session previews synthetic and read-only. |
| Role filtering | `./scripts/role-filter-check.sh` | passed | Yes | Keeps role filtering visibility-only. |
| Docs audit | `./scripts/docs-check.sh` and `./scripts/final-docs-audit.sh` | passed | Yes | Keeps release docs coherent and free of blocked markers. |
| Boundary check | `./scripts/verify-no-domain-drift.sh` and `./scripts/boundary-check.sh` | passed | Yes | Keeps domain and architecture boundaries intact. |
| Repository health | `./scripts/check.sh` | passed | Yes | Runs the full backend, SDK, type, architecture, and repo-health stack. |

## Evidence examples

- `examples/operator-console/operator-platform-regression-matrix.json`
- `examples/operator-console/operator-platform-freeze-gate-result.json`
- `examples/operator-console/operator-platform-regression-evidence.json`
