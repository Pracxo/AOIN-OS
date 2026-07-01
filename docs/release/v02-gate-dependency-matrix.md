# v0.2 Gate Dependency Matrix

## Purpose

This matrix maps candidate v0.2 workstreams to required prior gates, required
new gates, ADR dependencies, approval state, blockers, and release blockers.

| Workstream | Required Prior Gates | Required New Gates | Required ADR | Approved Today | Blocked Until | Release Blocker If Violated |
| --- | --- | --- | --- | --- | --- | --- |
| production auth implementation planning | release candidate gate, platform integration freeze, auth prototype review | production auth implementation gate, auth no-go regression | production auth implementation ADR | no | ADR and gates pass | production auth enabled or credentials/tokens stored |
| connector runtime implementation planning | release candidate gate, connector platform stabilization gate, platform integration freeze | connector runtime implementation gate, external-call no-go regression | connector runtime implementation ADR | no | ADR, egress/ingress, policy, audit evidence pass | connector runtime or external calls enabled |
| credential store implementation planning | release candidate gate, connector credential check, platform integration freeze | credential store implementation gate, protected-material no-go regression | credential store implementation ADR | no | ADR and lifecycle evidence pass | credentials or tokens stored |
| sandbox runtime implementation planning | release candidate gate, connector sandbox check, platform integration freeze | sandbox runtime implementation gate, isolation no-go regression | sandbox runtime implementation ADR | no | ADR and isolation evidence pass | sandbox execution or filesystem/network/process access enabled |
| operator write execution planning | release candidate gate, operator platform freeze gate, platform integration freeze | operator write execution gate, write-path no-go regression | operator write execution ADR | no | ADR, policy, rollback, and operator review pass | write execution, tool execution, or hard delete enabled |
| module activation implementation planning | release candidate gate, module activation design review, platform integration freeze | module activation implementation gate, activation no-go regression | module activation ADR | no | ADR, package trust, sandbox dependency, and policy evidence pass | code loading, runtime registration, or capability activation enabled |
| external call release gate planning | release candidate gate, connector release gate, platform integration freeze | external-call release gate, egress no-go regression | external calls release ADR | no | ADR, allowlist, redaction, policy, and rollback evidence pass | network client, provider SDK, endpoint, or external call added |
| audit/provenance hardening | release candidate gate, boundary check, docs audit | audit/provenance hardening gate | rollback/audit ADR | no | ADR and redaction/audit evidence pass | audit bypass, privileged bypass, raw secret exposure |
| rollback and recovery model | release candidate gate, platform integration freeze | rollback readiness gate | rollback/audit ADR | no | ADR and disable/recovery evidence pass | rollback-free execution or hard delete |
| static console to production UI decision | release candidate gate, static console safety check, UI release gate | production UI decision gate | production UI decision ADR | no | ADR and dependency review pass | frontend dependency, login, write control, or runtime route added |

## Matrix Rule

If any workstream changes from planning-only to implementation without its ADR
and gates passing, the release is blocked.
