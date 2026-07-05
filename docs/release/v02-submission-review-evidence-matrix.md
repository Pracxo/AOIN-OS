# v0.2 Submission Review Evidence Matrix

| Submission area | Required evidence | Required reviewer | Required ADR | Required gate | Submission approval state | Implementation approval state | Release blocker if violated | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Production auth | threat model, identity lifecycle, rollback, audit | security and architecture | future production auth implementation ADR | production auth implementation gate | false | false | true | production auth remains disabled |
| Connector runtime | policy, credential, sandbox, egress, audit | connector, security, policy | future connector runtime implementation ADR | connector runtime implementation gate | false | false | true | connector runtime remains disabled |
| Operator write execution | action review, approval, rollback, dry-run evidence | operator/platform and security | future operator write execution ADR | operator write execution gate | false | false | true | write execution remains disabled |
| Module activation | package, capability, code loading, registration evidence | architecture and policy | future module activation ADR | module activation gate | false | false | true | module activation remains disabled |
| External call release gate | egress inventory, provider boundary, no secret evidence | security and release governance | future external call release gate ADR | external call release gate | false | false | true | external calls remain absent |
| Credential store | secret handling, redaction, rotation, storage evidence | security and audit/provenance | future credential store implementation ADR | credential store implementation gate | false | false | true | credentials and tokens remain absent |
| Sandbox runtime | isolation, filesystem, network, process denial evidence | security and architecture | future sandbox runtime implementation ADR | sandbox runtime implementation gate | false | false | true | sandbox execution remains disabled |
| Production UI decision | static console, auth/session, accessibility evidence | operator/platform and release governance | future production UI decision ADR | production UI release gate | false | false | true | frontend dependencies remain absent |

## AION-135 Stabilization Handoff

AION-135 keeps this review evidence matrix as pre-approval planning evidence
and requires explicit ADR and gate dependencies before future implementation
review. Evidence completeness does not approve submissions, request packs,
pre-approval queue items, implementations, runtime, tags, or releases.
