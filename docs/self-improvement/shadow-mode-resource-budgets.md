# Shadow-Mode Resource Budgets

AION-177 authorizes these maximum budgets for a future AION-178 shadow-mode
implementation:

| Budget | Limit |
| --- | ---: |
| Maximum observation references | 1000 |
| Maximum evaluation records | 1000 |
| Maximum failure patterns | 100 |
| Maximum hypotheses | 50 |
| Maximum regression-test proposals | 25 |
| Maximum shadow proposals | 10 |
| Maximum concurrency | 4 |
| Maximum wall clock seconds | 1800 |
| Maximum benchmark cost units | 50 |
| Maximum output bytes | 10485760 |
| Maximum operator output files | 20 |
| Network calls | 0 |
| Git operations | 0 |
| Source mutations | 0 |
| Real pull requests | 0 |
| Runtime promotions | 0 |

Budget violations must fail closed into an operator-visible review item. They
must not trigger retry loops, source edits, Git activity, provider calls,
connector calls, deployment, canary exposure, or approval creation.

An exceeded budget must stop the run, fail closed, produce no implementation
authorization, produce no approval, produce no partial active-runtime change,
and create a redacted budget-failure record. A quality gain cannot override a
resource-budget violation.
## AION-178 Resource Budget Update

AION-178 enforces exact default budgets: 1000 observation references, 1000
evaluation records, 100 failure patterns, 50 hypotheses, 25 regression-test
proposals, 10 shadow proposals, 4 workers, 1800 wall-clock seconds, 50 cost
units, 10485760 output bytes, and 20 operator output files. Network calls, Git
operations, source mutations, real pull requests, and runtime promotions remain
zero-budget dimensions.
