# Rollback and Compensation Policy

A promotion transaction plan must include idempotency checks, rollback steps, and compensation steps before any later persistence task can be considered. Rollback planning is mandatory even when AION-222 remains write-disabled.

AION-222 may validate rollback and compensation plans in memory. It may not execute rollback against persistent knowledge, memory, source, Git, or production runtime.
