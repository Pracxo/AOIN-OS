# Secure Runtime Integration Evidence Matrix

| Evidence | Path | Required State |
| --- | --- | --- |
| Program charter | `docs/secure-runtime-integration/program-charter.md` | New separate program, no parent reopen |
| Program ledger | `docs/secure-runtime-integration/program-ledger.json` | `secure_runtime_foundation_implemented_local_operator_simulation_only_pending_closeout` |
| Authorization ledger | `docs/secure-runtime-integration/authorization-ledger.json` | Sole active `AION-230-SRI-0001` |
| AION-231 scope | `docs/secure-runtime-integration/architecture-roadmap.md` | AION-231 implemented, AION-233 through AION-238 unauthorized |
| Runtime boundary | `examples/secure-runtime-integration/runtime-boundary.json` | Disabled providers, connectors, tools, modules, production, release |
| Static console program | `operator-console-static/demo-data/secure-runtime-integration-program.json` | Read-only program evidence |
| Static console authorization | `operator-console-static/demo-data/secure-runtime-integration-authorization.json` | Read-only authorization evidence |
| Runtime hold script | `scripts/secure-runtime-integration-runtime-hold.sh` | Full check deferred only under nested gate |
| No-go script | `scripts/secure-runtime-integration-program-no-go-regression.sh` | Runtime/source/release violations fail |
| Authorization check | `scripts/secure-runtime-integration-program-authorization-check.sh` | Canonical fields and boundaries pass |

AION-232 remains the required formal AION-231 closeout and
next-authorization decision task.

All evidence remains local, static, redacted where applicable, and
non-activating.
