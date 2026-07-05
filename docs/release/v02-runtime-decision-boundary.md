# v0.2 Runtime Decision Boundary

## Boundary

AION-138 defines the runtime decision boundary for the decision package
preview. The boundary is intentionally locked: runtime decisions are future
approval subjects, not outcomes of this package.

## Candidate Boundary Table

| Candidate | Current decision state | Runtime state | AION-138 outcome |
| --- | --- | --- | --- |
| Production auth implementation | not approved | disabled | evidence only |
| Audit/provenance hardening | not approved | disabled | evidence only |
| Rollback/recovery implementation | not approved | disabled | evidence only |
| External call release gate | not approved | disabled | evidence only |
| Connector runtime implementation | not approved | disabled | evidence only |
| Credential store implementation | not approved | disabled | evidence only |
| Sandbox runtime implementation | not approved | disabled | evidence only |
| Operator write execution | not approved | disabled | evidence only |
| Module activation | not approved | disabled | evidence only |
| Production UI decision | not approved | disabled | evidence only |

## Enforcement Notes

- Future implementation still requires explicit approval records.
- Future approval still requires ADR dependency evidence.
- Future approval still requires gate dependency evidence.
- Future approval still requires security, architecture, operator, policy,
  rollback, and audit evidence.
- AION-138 cannot bypass missing evidence.
- AION-138 cannot create a release or tag.
