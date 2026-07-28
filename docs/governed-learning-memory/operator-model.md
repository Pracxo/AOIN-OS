# Governed Learning and Memory Operator Model

The operator reviews candidate lineage, evidence posture, approval evidence, conflict posture, version plans, memory projection plans, rollback plans, and integrity findings before any future persistence task can be considered.

AION-221 records `AION-221-GLM-0001` as active for `AION-222` only. The operator model requires separation of duties, approval expiry checks, approval revocation checks, and redacted review items. Runtime-created approvals are prohibited.

AION-222 outputs must remain dry-run and in-memory. They may prepare operator review records but may not write durable knowledge, cognitive memory, beliefs, source, Git state, or production runtime state.
