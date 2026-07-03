# v0.2 Candidate Workstream Evidence Baseline

Each candidate remains blocked with approval status false and implementation status false.

| Workstream | Proposal status | Approval status false | Implementation status false | Required ADR | Required gate | Required evidence | Blocker | Next planning action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| production auth implementation proposal | queued_for_future_decision | false | false | production auth implementation ADR | production auth implementation gate | identity threat model, session plan, rollback plan | production auth approval remains false | draft scoped auth ADR |
| audit/provenance hardening proposal | queued_for_future_decision | false | false | audit provenance hardening ADR | audit provenance release gate | audit chain model, retention plan, verification plan | hardening approval remains false | draft provenance evidence pack |
| rollback/recovery proposal | queued_for_future_decision | false | false | rollback recovery ADR | rollback recovery gate | recovery scope, rollback drills, operator review | recovery approval remains false | draft rollback matrix |
| external call release gate proposal | queued_for_future_decision | false | false | external call release ADR | external call release gate | egress policy, allowlist, audit trail | external calls remain absent | draft egress no-go evidence |
| connector runtime implementation proposal | queued_for_future_decision | false | false | connector runtime ADR | connector runtime release gate | connector threat model, credentials plan, sandbox plan | connector runtime remains disabled | draft connector runtime prerequisites |
| credential store implementation proposal | queued_for_future_decision | false | false | credential store ADR | credential store safety gate | secret lifecycle, redaction, revocation evidence | credential storage remains absent | draft credential storage plan |
| sandbox runtime implementation proposal | queued_for_future_decision | false | false | sandbox runtime ADR | sandbox runtime safety gate | isolation model, network/filesystem denial, audit plan | sandbox execution remains absent | draft sandbox boundary plan |
| operator write execution proposal | queued_for_future_decision | false | false | operator write execution ADR | operator write execution gate | dry-run evidence, approval model, rollback plan | write execution remains disabled | draft write-path approval plan |
| module activation proposal | queued_for_future_decision | false | false | module activation ADR | module activation gate | capability review, package denial, activation policy | module activation remains disabled | draft activation prerequisite plan |
| production UI decision proposal | queued_for_future_decision | false | false | production UI decision ADR | production UI release gate | UI scope, access model, no-write proof | production UI approval remains false | draft UI decision record |

## AION-128 Planning Master Use

AION-128 carries this candidate workstream evidence into the planning master
checkpoint. Every candidate remains blocked with approval status false,
implementation status false, approval queue item approval false, proposal
implementation approval false, and runtime implementation approval false.
