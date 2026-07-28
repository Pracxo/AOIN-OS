# Governed Learning and Memory Threat Model

## Primary Threats

- Treating a verified candidate as durable truth without approval and revalidation.
- Treating operator approval as factual proof.
- Losing source provenance, dissent, conflict, or rollback evidence.
- Writing cognitive memory before a separate persistence authorization exists.
- Creating automatic promotions from engagement signals.
- Letting runtime code create approvals, mutate source, mutate Git state, call tools, call providers, or activate production paths.

## Controls

AION-221 records explicit false runtime flags, zero-effect budgets, no AION-222 source files, inherited AION-220 closeout verification, and focused no-go scripts. AION-222 remains deterministic, dry-run, in-memory, approval-bound, and write-disabled.
