# v0.2 Submission Review Routing

Submission review routing assigns future implementation candidates to planning reviewers without approving implementation or enabling runtime.

| Submission type | Required reviewer roles | Required ADR | Required gate | Required evidence | Routing status | Implementation approval | Runtime enabled |
| --- | --- | --- | --- | --- | --- | --- | --- |
| production auth implementation candidate | Security reviewer, architecture reviewer, policy reviewer, auditor | production auth ADR update | production auth disabled gate | auth threat model, no credentials/tokens proof, local-session boundary | routed_for_review | false | false |
| audit/provenance hardening candidate | Audit/provenance reviewer, architecture reviewer, operator reviewer, auditor | audit/provenance ADR update | audit integrity gate | provenance matrix, ledger integrity evidence, docs audit evidence | routed_for_review | false | false |
| rollback/recovery candidate | Rollback reviewer, operator reviewer, architecture reviewer, auditor | rollback/recovery ADR update | rollback readiness gate | recovery scenarios, rollback evidence, no hard-delete proof | routed_for_review | false | false |
| external call release gate candidate | Security reviewer, policy reviewer, architecture reviewer, auditor | external call release ADR | external call no-go gate | egress boundary, provider abstinence proof, no network client proof | routed_for_review | false | false |
| connector runtime implementation candidate | Security reviewer, architecture reviewer, policy reviewer, auditor | connector runtime ADR update | connector runtime disabled gate | connector release gate, credential absence, sandbox absence | routed_for_review | false | false |
| credential store implementation candidate | Security reviewer, audit/provenance reviewer, policy reviewer, auditor | credential store ADR update | credential store no-go gate | redaction plan, secret lifecycle evidence, token absence proof | routed_for_review | false | false |
| sandbox runtime implementation candidate | Security reviewer, architecture reviewer, rollback reviewer, auditor | sandbox runtime ADR update | sandbox disabled gate | isolation model, no process spawn proof, no network proof | routed_for_review | false | false |
| operator write execution candidate | Operator reviewer, policy reviewer, rollback reviewer, auditor | operator write execution ADR update | write-path no-go gate | dry-run authorization, rollback model, no write execution proof | routed_for_review | false | false |
| module activation candidate | Architecture reviewer, security reviewer, operator reviewer, auditor | module activation ADR update | activation no-go gate | capability boundary, code loading absence, registration absence | routed_for_review | false | false |
| production UI decision candidate | Operator reviewer, architecture reviewer, policy reviewer, auditor | production UI ADR update | static console release gate | accessibility evidence, read-only proof, no frontend dependency proof | routed_for_review | false | false |

Routing readiness is not approval. Every row remains implementation approval false and runtime enabled false.
