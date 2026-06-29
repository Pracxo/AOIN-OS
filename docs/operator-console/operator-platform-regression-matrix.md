# Operator Platform Regression Matrix

## Purpose

AION-102 turns the AION-101 checkpoint into a repeatable stabilization gate.
The matrix defines the long-running checks that must stay green before future
Operator Platform, UI, auth, module, provider, or operator-action work moves
forward.

## Regression areas

| Regression area | Scripts | Expected result | Release blocker conditions | Frequency | Owner role | Evidence output |
| --- | --- | --- | --- | --- | --- | --- |
| Static console safety | `./scripts/static-console-safety-check.sh` | `Static console safety check PASS` | Any frontend dependency, build step, login form, write verb, external URL, activation, execution, provider-call, protected-output, or storage control appears. | Every PR and before phase handoff | Operator platform maintainer | `examples/operator-console/operator-platform-regression-evidence.json` |
| UI release gate | `./scripts/ui-release-gate.sh` | `UI release gate PASS` | Any static console release gate check fails. | Every PR and before phase handoff | Operator platform maintainer | `examples/operator-console/operator-platform-freeze-gate-result.json` |
| Module lifecycle dashboard | `./scripts/module-lifecycle-dashboard-check.sh` | `Module lifecycle dashboard check PASS` | Activation, execution, registration, code loading, or hidden blockers appear. | Every PR | Module governance reviewer | `examples/operator-console/operator-platform-regression-matrix.json` |
| Provider hardening dashboard | `./scripts/provider-dashboard-check.sh` | `Provider dashboard check PASS` | Provider invocation, external model call, provider credential flow, or provider-call control appears. | Every PR | Provider boundary reviewer | `examples/operator-console/operator-platform-regression-matrix.json` |
| Operator actions | `./scripts/operator-actions-check.sh` | `Operator actions check PASS` | Any operator action executes, mutates source records, or enables a write control. | Every PR | Operator action reviewer | `examples/operator-console/operator-platform-regression-matrix.json` |
| Action authorization | `./scripts/action-authorization-check.sh` | `Action authorization check PASS` | Dry-run authorization grants execution, activation, external calls, or privileged bypass. | Every PR | Policy reviewer | `examples/operator-console/operator-platform-regression-matrix.json` |
| Local auth | `./scripts/local-auth-check.sh` | `Local auth check PASS` | Dev-only identity simulation becomes production auth or stores credentials. | Every PR | Auth reviewer | `examples/operator-console/operator-platform-regression-matrix.json` |
| Local session | `./scripts/local-session-check.sh` | `Local session check PASS` | Session preview persists browser state or creates a production session. | Every PR | Auth reviewer | `examples/operator-console/operator-platform-regression-matrix.json` |
| Role filtering | `./scripts/role-filter-check.sh` | `Role filter check PASS` | Role visibility filtering hides forbidden actions or grants execution authority. | Every PR | Policy reviewer | `examples/operator-console/operator-platform-regression-matrix.json` |
| Production auth architecture | `./scripts/production-auth-architecture-check.sh` | `Production auth architecture check PASS` | Future auth design is treated as implemented runtime auth. | Every PR touching auth docs | Auth reviewer | `examples/operator-console/operator-platform-regression-matrix.json` |
| Disabled auth runtime | `./scripts/auth-runtime-check.sh` | `Auth runtime check PASS` | Auth runtime, external identity, login/logout, or session persistence is enabled. | Every PR | Auth reviewer | `examples/operator-console/operator-platform-freeze-gate-result.json` |
| Docs audit | `./scripts/docs-check.sh` and `./scripts/final-docs-audit.sh` | Docs checks pass | Release docs drift, blocked markers appear, or production UI claims appear. | Every PR | Release reviewer | `examples/operator-console/operator-platform-regression-evidence.json` |
| Boundary check | `./scripts/boundary-check.sh` | Boundary tests pass | Vendor leakage, architecture boundary drift, or external adapter exposure appears. | Every PR | Architecture reviewer | `examples/operator-console/operator-platform-regression-evidence.json` |
| Repository health | `./scripts/check.sh` | Full check succeeds | Backend tests, SDK tests, type checks, lint, architecture checks, or repo health fail. | Before merge and phase handoff | Release reviewer | `examples/operator-console/operator-platform-freeze-gate-result.json` |

## Stabilization command

Run the full stabilization matrix with:

```bash
./scripts/operator-platform-regression.sh
```

The regression matrix is intentionally composed from existing local checks. It
does not add runtime capability, frontend dependencies, production auth,
activation, execution, provider calls, external calls, package installation, or
privileged bypass.
