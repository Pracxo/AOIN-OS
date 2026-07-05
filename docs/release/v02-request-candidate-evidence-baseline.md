# v0.2 Request Candidate Evidence Baseline

Every request candidate remains unapproved. Each candidate must collect
evidence before future review and must keep submission approval false and
implementation approval false.

| Candidate ID | Workstream | Submission status | Submission approval | Implementation approval | Required ADR | Required gate | Required evidence | Blocker | Next planning action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V02-CAND-PROD-AUTH | production auth implementation candidate | drafted | false | false | Future production auth implementation ADR | Production auth implementation gate | threat model, identity lifecycle, rollback, audit, no-go acknowledgement | production auth remains disabled | draft auth implementation evidence pack |
| V02-CAND-AUDIT-PROV | audit/provenance hardening candidate | drafted | false | false | Future audit/provenance hardening ADR | Audit provenance hardening gate | integrity evidence, retention evidence, reviewer notes, rollback evidence | no implementation approval record | map audit hardening evidence gaps |
| V02-CAND-ROLLBACK | rollback/recovery candidate | drafted | false | false | Future rollback recovery ADR | Rollback recovery gate | restore evidence, failure-mode evidence, operator review, release blocker list | recovery runtime remains unimplemented | define rollback verification matrix |
| V02-CAND-EXT-CALL-GATE | external call release gate candidate | drafted | false | false | Future external call release gate ADR | External call release gate | egress inventory, provider boundary evidence, no secret evidence, policy review | external calls remain absent | draft external call approval prerequisites |
| V02-CAND-CONN-RUNTIME | connector runtime implementation candidate | drafted | false | false | Future connector runtime implementation ADR | Connector runtime implementation gate | connector policy, sandbox, credential, egress, audit, rollback evidence | connector runtime remains disabled | assemble connector runtime request evidence |
| V02-CAND-CRED-STORE | credential store implementation candidate | drafted | false | false | Future credential store implementation ADR | Credential store implementation gate | secret handling, redaction, rotation, storage, audit, denial evidence | credentials/tokens remain absent | draft credential store security evidence |
| V02-CAND-SANDBOX | sandbox runtime implementation candidate | drafted | false | false | Future sandbox runtime implementation ADR | Sandbox runtime implementation gate | isolation, filesystem, network, process, package-install denial evidence | sandbox execution remains disabled | define sandbox safety evidence matrix |
| V02-CAND-OP-WRITE | operator write execution candidate | drafted | false | false | Future operator write execution ADR | Operator write execution gate | action review, approval, rollback, dry-run, audit, human-control evidence | operator write paths remain disabled | prepare write-path approval evidence |
| V02-CAND-MODULE-ACT | module activation candidate | drafted | false | false | Future module activation ADR | Module activation gate | package, capability, code loading, registration, policy, audit evidence | module activation remains disabled | draft activation dependency checklist |
| V02-CAND-PROD-UI | production UI decision candidate | drafted | false | false | Future production UI decision ADR | Production UI release gate | static console evidence, auth/session evidence, accessibility, release blocker list | frontend dependencies remain absent | define production UI decision evidence |

## Boundary

No candidate status approves implementation or enables runtime. Candidates can
advance only as planning records until explicit approval records, ADRs, and
gate evidence exist in a future milestone.

## AION-135 Closeout Handoff

AION-135 closes out these request candidates into
`docs/release/v02-request-candidate-closeout-baseline.md`. Each candidate keeps
submission approval false, implementation approval false, pre-approval queue
approval false, runtime approval false, and a blocker plus next planning
action.
